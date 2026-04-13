from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List


class Workout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    muscle_group: str = ""   # e.g. Chest, Legs, Back, Core, Arms, Cardio
    difficulty: str = "Beginner"  # Beginner, Intermediate, Advanced
    duration_minutes: int = 30
    equipment: str = "None"

    # Relationship to RoutineWorkout junction
    routine_workouts: List["RoutineWorkout"] = Relationship(back_populates="workout")


class Routine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    user: Optional["User"] = Relationship(back_populates="routines")
    routine_workouts: List["RoutineWorkout"] = Relationship(back_populates="routine")


class RoutineWorkout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id")
    workout_id: int = Field(foreign_key="workout.id")
    sets: int = 3
    reps: int = 10
    notes: str = ""

    routine: Optional[Routine] = Relationship(back_populates="routine_workouts")
    workout: Optional[Workout] = Relationship(back_populates="routine_workouts")
