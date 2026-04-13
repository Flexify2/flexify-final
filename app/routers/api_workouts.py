from fastapi import Request
from fastapi.responses import JSONResponse
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.workout import WorkoutRepository
from . import api_router


@api_router.get("/workouts")
async def api_get_workouts(user: AuthDep, db: SessionDep, muscle_group: str = "", difficulty: str = ""):
    repo = WorkoutRepository(db)
    workouts = repo.get_all_workouts(muscle_group=muscle_group, difficulty=difficulty)
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "muscle_group": w.muscle_group,
            "difficulty": w.difficulty,
            "duration_minutes": w.duration_minutes,
            "equipment": w.equipment,
        }
        for w in workouts
    ]


@api_router.get("/routines")
async def api_get_routines(user: AuthDep, db: SessionDep):
    repo = WorkoutRepository(db)
    routines = repo.get_user_routines(user.id)
    result = []
    for r in routines:
        rws = repo.get_routine_workouts(r.id)
        result.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "workout_count": len(rws),
        })
    return result
