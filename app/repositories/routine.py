import logging

from sqlmodel import Session, func, select

from app.models.workout import Routine, RoutineWorkout, Workout
from app.schemas.routine import WorkoutInRoutine

logger = logging.getLogger(__name__)


class RoutineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_for_user(
        self,
        user_id: int,
        query: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 9,
    ) -> tuple[list[tuple[Routine, int]], int]:
        count_stmt = select(func.count()).select_from(Routine).where(Routine.user_id == user_id)
        if query:
            count_stmt = count_stmt.where(Routine.name.ilike(f"%{query}%"))

        total_items = int(self.db.exec(count_stmt).one())

        sort_col = Routine.name if sort_by == "name" else Routine.created_at
        order_clause = sort_col.desc() if sort_dir == "desc" else sort_col.asc()

        offset = (page - 1) * page_size
        list_stmt = (
            select(Routine, func.count(RoutineWorkout.id))
            .outerjoin(RoutineWorkout, RoutineWorkout.routine_id == Routine.id)
            .where(Routine.user_id == user_id)
            .group_by(Routine.id)
            .order_by(order_clause)
            .offset(offset)
            .limit(page_size)
        )
        if query:
            list_stmt = list_stmt.where(Routine.name.ilike(f"%{query}%"))

        rows = self.db.exec(list_stmt).all()
        return [(routine, int(workout_count or 0)) for routine, workout_count in rows], total_items

    def get_by_id(self, routine_id: int) -> Routine | None:
        return self.db.get(Routine, routine_id)

    def create(self, name: str, description: str, user_id: int) -> Routine:
        routine = Routine(name=name, description=description, user_id=user_id)
        try:
            self.db.add(routine)
            self.db.commit()
            self.db.refresh(routine)
            return routine
        except Exception as e:
            logger.error("Error creating routine: %s", e)
            self.db.rollback()
            raise

    def update(self, routine_id: int, name: str, description: str | None = None) -> Routine:
        routine = self.db.get(Routine, routine_id)
        if not routine:
            raise Exception("Routine not found")
        routine.name = name
        if description is not None:
            routine.description = description
        try:
            self.db.add(routine)
            self.db.commit()
            self.db.refresh(routine)
            return routine
        except Exception as e:
            logger.error("Error updating routine: %s", e)
            self.db.rollback()
            raise

    def delete(self, routine_id: int) -> None:
        routine = self.db.get(Routine, routine_id)
        if not routine:
            raise Exception("Routine not found")

        rw_list = self.db.exec(select(RoutineWorkout).where(RoutineWorkout.routine_id == routine_id)).all()
        for rw in rw_list:
            self.db.delete(rw)
        self.db.delete(routine)
        try:
            self.db.commit()
        except Exception as e:
            logger.error("Error deleting routine: %s", e)
            self.db.rollback()
            raise

    def add_workout(self, routine_id: int, workout_id: int, sets: int = 3, reps: int = 10, order: int = 0) -> RoutineWorkout:
        rw = RoutineWorkout(routine_id=routine_id, workout_id=workout_id, sets=sets, reps=reps, order=order)
        try:
            self.db.add(rw)
            self.db.commit()
            self.db.refresh(rw)
            return rw
        except Exception as e:
            logger.error("Error adding workout to routine: %s", e)
            self.db.rollback()
            raise

    def remove_workout(self, routine_workout_id: int) -> None:
        rw = self.db.get(RoutineWorkout, routine_workout_id)
        if not rw:
            raise Exception("Routine workout not found")
        try:
            self.db.delete(rw)
            self.db.commit()
        except Exception as e:
            logger.error("Error removing workout from routine: %s", e)
            self.db.rollback()
            raise

    def update_routine_workout(self, routine_workout_id: int, sets: int | None = None, reps: int | None = None) -> RoutineWorkout:
        rw = self.db.get(RoutineWorkout, routine_workout_id)
        if not rw:
            raise Exception("Routine workout not found")
        if sets is not None:
            rw.sets = sets
        if reps is not None:
            rw.reps = reps
        try:
            self.db.add(rw)
            self.db.commit()
            self.db.refresh(rw)
            return rw
        except Exception as e:
            logger.error("Error updating routine workout: %s", e)
            self.db.rollback()
            raise

    def get_workouts_in_routine(self, routine_id: int) -> list[WorkoutInRoutine]:
        stmt = (
            select(RoutineWorkout, Workout)
            .join(Workout, RoutineWorkout.workout_id == Workout.id)
            .where(RoutineWorkout.routine_id == routine_id)
            .order_by(RoutineWorkout.order)
        )
        rows = self.db.exec(stmt).all()
        result = []
        for rw, workout in rows:
            result.append(
                WorkoutInRoutine(
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
            )
        return result
