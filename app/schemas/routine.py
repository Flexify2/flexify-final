from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class RoutineCreate(SQLModel):
    name: str
    description: str = ""


class RoutineUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoutineWorkoutCreate(SQLModel):
    workout_id: int
    sets: int = 3
    reps: int = 10
    order: int = 0


class RoutineExternalWorkoutCreate(SQLModel):
    name: str
    description: str = ""
    muscle_group: str
    category: str = "Strength"
    image_url: Optional[str] = None
    sets: int = 3
    reps: int = 10


class RoutineWorkoutUpdate(SQLModel):
    sets: Optional[int] = None
    reps: Optional[int] = None
    order: Optional[int] = None


class WorkoutInRoutine(SQLModel):
    id: int
    routine_workout_id: int
    name: str
    description: str
    muscle_group: str
    category: str
    sets: int
    reps: int
    order: int
    image_url: Optional[str] = None


class RoutineResponse(SQLModel):
    id: int
    name: str
    description: str = ""
    user_id: int
    created_at: datetime
    workout_count: int = 0


class RoutineListResponse(SQLModel):
    items: list[RoutineResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class RoutineDetailResponse(SQLModel):
    id: int
    name: str
    description: str = ""
    user_id: int
    created_at: datetime
    workouts: list[WorkoutInRoutine] = []
