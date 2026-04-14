from fastapi import Depends, Query, Request, Response
from fastapi.responses import Response as RawResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.workout import WorkoutRepository
from app.schemas.workout import ExternalWorkoutResponse, WorkoutResponse
from app.services.exercise_search_service import ExerciseSearchService
from app.services.workout_service import WorkoutService
from .router_utils import get_search_service
from . import api_router


def _get_service(db: SessionDep, search_service: ExerciseSearchService = Depends(get_search_service)) -> WorkoutService:
    return WorkoutService(WorkoutRepository(db), search_service)


@api_router.get("/workouts")
async def api_get_workouts(
    user: AuthDep,
    db: SessionDep,
    muscle_group: str = "",
    difficulty: str = "",
    q: str = "",
    category: str = "",
):
    repo = WorkoutRepository(db)
    workouts = repo.get_all_workouts(muscle_group=muscle_group, difficulty=difficulty) if not q and not category else repo.search(
        query=q,
        muscle_group=muscle_group,
        category=category,
    )
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "muscle_group": w.muscle_group,
            "category": w.category,
            "difficulty": w.difficulty,
            "duration_minutes": w.duration_minutes,
            "equipment": w.equipment,
            "image_url": w.image_url,
        }
        for w in workouts
    ]


@api_router.get("/workouts/external/search", response_model=list[ExternalWorkoutResponse])
async def search_external_workouts(
    request: Request,
    response: Response,
    user: AuthDep,
    service: WorkoutService = Depends(_get_service),
    q: str = Query(default="", max_length=120),
    muscle_group: str = Query(default="", max_length=60),
    category: str = Query(default="", max_length=60),
    equipment: str = Query(default="", max_length=60),
    difficulty: str = Query(default="", max_length=30),
    limit: int = Query(default=10, ge=1, le=30),
):
    response.headers["Cache-Control"] = "private, max-age=120"
    return await service.search_external(
        query=q,
        muscle_group=muscle_group,
        category=category,
        equipment=equipment,
        difficulty=difficulty,
        limit=limit,
    )


@api_router.get("/workouts/external/{exercise_id}/preview.gif")
async def external_workout_preview(
    exercise_id: str,
    request: Request,
    response: Response,
    user: AuthDep,
    search_service: ExerciseSearchService = Depends(get_search_service),
):
    response.headers["Cache-Control"] = "private, max-age=300"
    content = await search_service.get_preview_gif(exercise_id, resolution=180)
    if not content:
        return RawResponse(status_code=404)
    return RawResponse(content=content, media_type="image/gif")


@api_router.get("/workouts/external/{exercise_id}")
async def get_external_workout_detail(
    exercise_id: str,
    request: Request,
    response: Response,
    user: AuthDep,
    search_service: ExerciseSearchService = Depends(get_search_service),
):
    response.headers["Cache-Control"] = "private, max-age=300"
    detail = await search_service.get_exercise_detail(exercise_id)
    if not detail:
        return RawResponse(status_code=404)
    return detail


@api_router.get("/workouts/{workout_id}/alternatives", response_model=list[WorkoutResponse])
async def get_alternatives(
    workout_id: int,
    request: Request,
    user: AuthDep,
    service: WorkoutService = Depends(_get_service),
):
    return await service.get_alternatives(workout_id)
