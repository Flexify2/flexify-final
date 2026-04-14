from typing import Optional
from sqlmodel import SQLModel


class WorkoutCreate(SQLModel):
    name: str
    description: str = ""
    muscle_group: str
    category: str = "Strength"
    difficulty: str = "Beginner"
    duration_minutes: int = 30
    equipment: str = "None"


class WorkoutResponse(SQLModel):
    id: int
    name: str
    description: str
    muscle_group: str
    category: str = "Strength"
    difficulty: str = "Beginner"
    duration_minutes: int = 30
    equipment: str = "None"
    source: str = "local"


class ExternalWorkoutResponse(SQLModel):
    id: Optional[str] = None
    name: str
    description: str
    muscle_group: str
    category: str
    equipment: Optional[str] = None
    difficulty: Optional[str] = None
    instructions: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    source: str = "external"
