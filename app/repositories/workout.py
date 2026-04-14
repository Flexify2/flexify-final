from sqlmodel import Session, select
from app.models.workout import Workout, Routine, RoutineWorkout
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class WorkoutRepository:
    def __init__(self, db: Session):
        self.db = db

    # ─── Workouts ───────────────────────────────────────────────────────────

    def get_all_workouts(self, muscle_group: str = "", difficulty: str = "") -> List[Workout]:
        qry = select(Workout)
        if muscle_group:
            qry = qry.where(Workout.muscle_group == muscle_group)
        if difficulty:
            qry = qry.where(Workout.difficulty == difficulty)
        return self.db.exec(qry).all()

    def get_workout_by_id(self, workout_id: int) -> Optional[Workout]:
        return self.db.get(Workout, workout_id)

    def get_by_id(self, workout_id: int) -> Optional[Workout]:
        return self.get_workout_by_id(workout_id)

    def get_by_muscle_group(self, muscle_group: str) -> List[Workout]:
        return self.db.exec(select(Workout).where(Workout.muscle_group == muscle_group)).all()

    def get_by_name_and_muscle_group(self, name: str, muscle_group: str) -> Optional[Workout]:
        stmt = select(Workout).where(Workout.name == name, Workout.muscle_group == muscle_group)
        return self.db.exec(stmt).first()

    def create_workout(self, workout: Workout) -> Workout:
        try:
            self.db.add(workout)
            self.db.commit()
            self.db.refresh(workout)
            return workout
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating workout: {e}")
            raise

    def create(self, workout_data: dict) -> Workout:
        workout = Workout.model_validate(workout_data)
        return self.create_workout(workout)

    def update_workout(self, workout_id: int, data: dict) -> Workout:
        workout = self.db.get(Workout, workout_id)
        if not workout:
            raise Exception("Workout not found")
        for key, val in data.items():
            if val is not None:
                setattr(workout, key, val)
        try:
            self.db.add(workout)
            self.db.commit()
            self.db.refresh(workout)
            return workout
        except Exception as e:
            self.db.rollback()
            raise

    def delete_workout(self, workout_id: int):
        workout = self.db.get(Workout, workout_id)
        if not workout:
            raise Exception("Workout not found")
        try:
            self.db.delete(workout)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise

    def search(self, query: str = "", muscle_group: str = "", category: str = "") -> List[Workout]:
        stmt = select(Workout)
        if query:
            stmt = stmt.where(Workout.name.ilike(f"%{query}%"))
        if muscle_group:
            stmt = stmt.where(Workout.muscle_group == muscle_group)
        if category:
            stmt = stmt.where(Workout.category == category)
        return self.db.exec(stmt).all()

    def delete_unlinked_workouts(self) -> int:
        linked_workout_ids = self.db.exec(select(RoutineWorkout.workout_id)).all()
        linked_set = {workout_id for workout_id in linked_workout_ids if workout_id is not None}
        stmt = select(Workout)
        if linked_set:
            stmt = stmt.where(Workout.id.notin_(linked_set))

        to_delete = self.db.exec(stmt).all()
        count = len(to_delete)
        for workout in to_delete:
            self.db.delete(workout)

        if count:
            self.db.commit()
        return count

    # ─── Routines ───────────────────────────────────────────────────────────

    def get_user_routines(self, user_id: int) -> List[Routine]:
        return self.db.exec(select(Routine).where(Routine.user_id == user_id)).all()

    def get_routine_by_id(self, routine_id: int) -> Optional[Routine]:
        return self.db.get(Routine, routine_id)

    def create_routine(self, name: str, description: str, user_id: int) -> Routine:
        routine = Routine(name=name, description=description, user_id=user_id)
        try:
            self.db.add(routine)
            self.db.commit()
            self.db.refresh(routine)
            return routine
        except Exception as e:
            self.db.rollback()
            raise

    def update_routine(self, routine_id: int, name: str, description: str) -> Routine:
        routine = self.db.get(Routine, routine_id)
        if not routine:
            raise Exception("Routine not found")
        routine.name = name
        routine.description = description
        try:
            self.db.add(routine)
            self.db.commit()
            self.db.refresh(routine)
            return routine
        except Exception as e:
            self.db.rollback()
            raise

    def delete_routine(self, routine_id: int):
        routine = self.db.get(Routine, routine_id)
        if not routine:
            raise Exception("Routine not found")
        try:
            # Delete junction rows first
            rws = self.db.exec(select(RoutineWorkout).where(RoutineWorkout.routine_id == routine_id)).all()
            for rw in rws:
                self.db.delete(rw)
            self.db.delete(routine)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise

    # ─── RoutineWorkout (junction) ──────────────────────────────────────────

    def get_routine_workouts(self, routine_id: int) -> List[RoutineWorkout]:
        return self.db.exec(
            select(RoutineWorkout).where(RoutineWorkout.routine_id == routine_id)
        ).all()

    def add_workout_to_routine(self, routine_id: int, workout_id: int, sets: int, reps: int, notes: str = "") -> RoutineWorkout:
        rw = RoutineWorkout(routine_id=routine_id, workout_id=workout_id, sets=sets, reps=reps, notes=notes)
        try:
            self.db.add(rw)
            self.db.commit()
            self.db.refresh(rw)
            return rw
        except Exception as e:
            self.db.rollback()
            raise

    def remove_workout_from_routine(self, routine_workout_id: int):
        rw = self.db.get(RoutineWorkout, routine_workout_id)
        if not rw:
            raise Exception("Not found")
        try:
            self.db.delete(rw)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise

    def get_routine_workout_by_id(self, rw_id: int) -> Optional[RoutineWorkout]:
        return self.db.get(RoutineWorkout, rw_id)
