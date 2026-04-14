import asyncio

from fastapi import HTTPException, status

from app.repositories.routine import RoutineRepository
from app.repositories.workout import WorkoutRepository
from app.schemas.routine import RoutineDetailResponse, RoutineListResponse, RoutineResponse, WorkoutInRoutine
from app.utilities.pagination import Pagination


class RoutineService:
    def __init__(self, routine_repo: RoutineRepository, workout_repo: WorkoutRepository, exercise_search_service=None):
        self.routine_repo = routine_repo
        self.workout_repo = workout_repo
        self.exercise_search_service = exercise_search_service

    def get_user_routines(
        self,
        user_id: int,
        query: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 9,
    ) -> RoutineListResponse:
        rows, total_items = self.routine_repo.get_all_for_user(
            user_id=user_id,
            query=query,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        pagination = Pagination(total_items, page, page_size)
        items = [
            RoutineResponse(**routine.model_dump(), workout_count=workout_count)
            for routine, workout_count in rows
        ]
        return RoutineListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=pagination.total_pages,
        )

    async def get_routine(self, routine_id: int, user_id: int) -> RoutineDetailResponse:
        routine = self.routine_repo.get_by_id(routine_id)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        if routine.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workouts = self.routine_repo.get_workouts_in_routine(routine_id)
        workouts = await self._hydrate_workout_images(workouts)
        return RoutineDetailResponse(**routine.model_dump(), workouts=workouts)

    async def _hydrate_workout_images(self, workouts: list[WorkoutInRoutine]) -> list[WorkoutInRoutine]:
        if not self.exercise_search_service or not getattr(self.exercise_search_service, "enabled", False):
            return workouts

        async def resolve_image(workout: WorkoutInRoutine) -> str | None:
            results = await self.exercise_search_service.search_exercises(
                name=workout.name,
                muscle=workout.muscle_group,
                exercise_type=workout.category,
                limit=1,
            )
            if not results:
                return None
            return results[0].image_url

        image_urls = await asyncio.gather(*(resolve_image(workout) for workout in workouts))
        hydrated: list[WorkoutInRoutine] = []
        for workout, image_url in zip(workouts, image_urls):
            hydrated.append(workout.model_copy(update={"image_url": image_url}))
        return hydrated

    def create_routine(self, name: str, description: str, user_id: int) -> RoutineResponse:
        routine = self.routine_repo.create(name=name, description=description, user_id=user_id)
        return RoutineResponse(**routine.model_dump())

    def update_routine(self, routine_id: int, name: str, description: str | None, user_id: int) -> RoutineResponse:
        routine = self.routine_repo.get_by_id(routine_id)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        if routine.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        updated = self.routine_repo.update(routine_id, name, description)
        return RoutineResponse(**updated.model_dump())

    def delete_routine(self, routine_id: int, user_id: int) -> None:
        routine = self.routine_repo.get_by_id(routine_id)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        if routine.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        self.routine_repo.delete(routine_id)

    def add_workout_to_routine(self, routine_id: int, workout_id: int, sets: int, reps: int, user_id: int) -> WorkoutInRoutine:
        routine = self.routine_repo.get_by_id(routine_id)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        if routine.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workout = self.workout_repo.get_by_id(workout_id)
        if not workout:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

        current = self.routine_repo.get_workouts_in_routine(routine_id)
        order = len(current)
        rw = self.routine_repo.add_workout(routine_id, workout_id, sets=sets, reps=reps, order=order)
        return WorkoutInRoutine(
            id=workout.id,
            routine_workout_id=rw.id,
            name=workout.name,
            description=workout.description,
            muscle_group=workout.muscle_group,
            category=workout.category,
            sets=rw.sets,
            reps=rw.reps,
            order=rw.order,
        )

    def add_external_workout_to_routine(
        self,
        routine_id: int,
        name: str,
        description: str,
        muscle_group: str,
        category: str,
        sets: int,
        reps: int,
        user_id: int,
    ) -> WorkoutInRoutine:
        existing = self.workout_repo.get_by_name_and_muscle_group(name, muscle_group)
        if existing:
            workout_id = existing.id
        else:
            created = self.workout_repo.create(
                {
                    "name": name,
                    "description": description,
                    "muscle_group": muscle_group,
                    "category": category,
                    "difficulty": "Intermediate",
                    "equipment": "Mixed",
                }
            )
            workout_id = created.id

        return self.add_workout_to_routine(
            routine_id=routine_id,
            workout_id=workout_id,
            sets=sets,
            reps=reps,
            user_id=user_id,
        )

    def remove_workout_from_routine(self, routine_workout_id: int, routine_id: int, user_id: int) -> None:
        routine = self.routine_repo.get_by_id(routine_id)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        if routine.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        self.routine_repo.remove_workout(routine_workout_id)

    def update_routine_workout(
        self,
        routine_workout_id: int,
        routine_id: int,
        user_id: int,
        sets: int | None = None,
        reps: int | None = None,
    ) -> WorkoutInRoutine:
        routine = self.routine_repo.get_by_id(routine_id)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        if routine.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        rw = self.routine_repo.update_routine_workout(routine_workout_id, sets=sets, reps=reps)
        workout = self.workout_repo.get_by_id(rw.workout_id)
        return WorkoutInRoutine(
            id=workout.id,
            routine_workout_id=rw.id,
            name=workout.name,
            description=workout.description,
            muscle_group=workout.muscle_group,
            category=workout.category,
            sets=rw.sets,
            reps=rw.reps,
            order=rw.order,
        )
