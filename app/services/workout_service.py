from app.repositories.workout import WorkoutRepository
from app.schemas.workout import ExternalWorkoutResponse, WorkoutResponse
from app.services.exercise_search_service import ExerciseSearchService


class WorkoutService:
    def __init__(self, workout_repo: WorkoutRepository, exercise_search_service: ExerciseSearchService | None = None):
        self.workout_repo = workout_repo
        self.exercise_search_service = exercise_search_service

    def get_all(self, query: str = "", muscle_group: str = "", category: str = "") -> list[WorkoutResponse]:
        workouts = self.workout_repo.search(query=query, muscle_group=muscle_group, category=category)
        return [WorkoutResponse(**w.model_dump()) for w in workouts]

    async def search_external(
        self,
        *,
        query: str = "",
        muscle_group: str = "",
        category: str = "",
        equipment: str = "",
        difficulty: str = "",
        limit: int = 10,
    ) -> list[ExternalWorkoutResponse]:
        if not self.exercise_search_service or not self.exercise_search_service.enabled:
            return self._search_local_as_external(query=query, muscle_group=muscle_group, category=category, limit=limit)

        try:
            results = await self.exercise_search_service.search_exercises(
                name=query,
                muscle=muscle_group,
                exercise_type=category,
                equipment=equipment,
                difficulty=difficulty,
                limit=limit,
            )
        except Exception:
            return self._search_local_as_external(query=query, muscle_group=muscle_group, category=category, limit=limit)

        if results:
            return results
        return self._search_local_as_external(query=query, muscle_group=muscle_group, category=category, limit=limit)

    def _search_local_as_external(
        self,
        *,
        query: str = "",
        muscle_group: str = "",
        category: str = "",
        limit: int = 10,
    ) -> list[ExternalWorkoutResponse]:
        workouts = self.workout_repo.search(query=query, muscle_group=muscle_group, category=category)
        return [
            ExternalWorkoutResponse(
                id=str(workout.id),
                name=workout.name,
                description=workout.description,
                muscle_group=workout.muscle_group,
                category=workout.category,
                equipment=workout.equipment,
                difficulty=workout.difficulty,
                source="local",
            )
            for workout in workouts[:limit]
        ]

    async def get_alternatives(self, workout_id: int) -> list[WorkoutResponse]:
        workout = self.workout_repo.get_by_id(workout_id)
        if not workout:
            raise Exception("Workout not found")

        alternatives = self.workout_repo.get_by_muscle_group(workout.muscle_group)
        results = [WorkoutResponse(**w.model_dump()) for w in alternatives if w.id != workout_id]

        external = await self.search_external(muscle_group=workout.muscle_group, category=workout.category, limit=8)
        existing_names = {w.name.lower() for w in results}
        existing_names.add(workout.name.lower())
        for candidate in external:
            if candidate.name.lower() in existing_names:
                continue
            local = self._get_or_create_local_from_external(candidate)
            results.append(local)
            existing_names.add(candidate.name.lower())

        return results

    def _get_or_create_local_from_external(self, external_workout: ExternalWorkoutResponse) -> WorkoutResponse:
        existing = self.workout_repo.get_by_name_and_muscle_group(
            external_workout.name,
            external_workout.muscle_group,
        )
        if existing:
            return WorkoutResponse(**existing.model_dump())

        created = self.workout_repo.create(
            {
                "name": external_workout.name,
                "description": external_workout.description,
                "muscle_group": external_workout.muscle_group,
                "category": external_workout.category or "Strength",
                "difficulty": external_workout.difficulty or "Intermediate",
                "equipment": external_workout.equipment or "Mixed",
            }
        )
        return WorkoutResponse(**created.model_dump())

    def purge_unlinked_local_workouts(self) -> int:
        return self.workout_repo.delete_unlinked_workouts()
