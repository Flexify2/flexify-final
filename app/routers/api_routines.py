from fastapi import HTTPException, Query, Request, status

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.routine import RoutineRepository
from app.repositories.workout import WorkoutRepository
from app.schemas.routine import (
    RoutineCreate,
    RoutineDetailResponse,
    RoutineExternalWorkoutCreate,
    RoutineListResponse,
    RoutineResponse,
    RoutineUpdate,
    RoutineWorkoutCreate,
    RoutineWorkoutUpdate,
    WorkoutInRoutine,
)
from app.services.routine_service import RoutineService
from . import api_router
from .api_workouts import _get_search_service


def _get_service(db: SessionDep) -> RoutineService:
    return RoutineService(RoutineRepository(db), WorkoutRepository(db))


def _require_user_id(user: AuthDep) -> int:
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user.id


async def _list_routines_impl(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    q: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=24),
):
    user_id = _require_user_id(user)
    if sort_by not in {"created_at", "name"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_by must be one of: created_at, name",
        )
    if sort_dir not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_dir must be one of: asc, desc",
        )
    return _get_service(db).get_user_routines(
        user_id=user_id,
        query=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


@api_router.get("/routines", response_model=RoutineListResponse)
async def list_routines(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    q: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=24),
):
    return await _list_routines_impl(request, db, user, q, sort_by, sort_dir, page, page_size)


@api_router.get("/routines/list", response_model=RoutineListResponse)
async def list_routines_legacy(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    q: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=24),
):
    return await _list_routines_impl(request, db, user, q, sort_by, sort_dir, page, page_size)


@api_router.post("/routines", response_model=RoutineResponse, status_code=status.HTTP_201_CREATED)
async def create_routine(request: Request, db: SessionDep, user: AuthDep, body: RoutineCreate):
    return _get_service(db).create_routine(name=body.name, description=body.description, user_id=_require_user_id(user))


@api_router.get("/routines/{routine_id}", response_model=RoutineDetailResponse)
async def get_routine(routine_id: int, request: Request, db: SessionDep, user: AuthDep):
    return await RoutineService(RoutineRepository(db), WorkoutRepository(db), _get_search_service()).get_routine(routine_id, _require_user_id(user))


@api_router.patch("/routines/{routine_id}", response_model=RoutineResponse)
async def update_routine(routine_id: int, request: Request, db: SessionDep, user: AuthDep, body: RoutineUpdate):
    if not body.name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required")
    return _get_service(db).update_routine(routine_id, body.name, body.description, _require_user_id(user))


@api_router.delete("/routines/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine(routine_id: int, request: Request, db: SessionDep, user: AuthDep):
    _get_service(db).delete_routine(routine_id, _require_user_id(user))


@api_router.post("/routines/{routine_id}/workouts", response_model=WorkoutInRoutine, status_code=status.HTTP_201_CREATED)
async def add_workout_to_routine(
    routine_id: int,
    request: Request,
    db: SessionDep,
    user: AuthDep,
    body: RoutineWorkoutCreate,
):
    user_id = _require_user_id(user)
    return _get_service(db).add_workout_to_routine(
        routine_id=routine_id,
        workout_id=body.workout_id,
        sets=body.sets,
        reps=body.reps,
        user_id=user_id,
    )


@api_router.post("/routines/{routine_id}/workouts/external", response_model=WorkoutInRoutine, status_code=status.HTTP_201_CREATED)
async def add_external_workout_to_routine(
    routine_id: int,
    request: Request,
    db: SessionDep,
    user: AuthDep,
    body: RoutineExternalWorkoutCreate,
):
    user_id = _require_user_id(user)
    return _get_service(db).add_external_workout_to_routine(
        routine_id=routine_id,
        name=body.name,
        description=body.description,
        muscle_group=body.muscle_group,
        category=body.category,
        image_url=body.image_url,
        sets=body.sets,
        reps=body.reps,
        user_id=user_id,
    )


@api_router.patch("/routines/{routine_id}/workouts/{routine_workout_id}", response_model=WorkoutInRoutine)
async def update_routine_workout(
    routine_id: int,
    routine_workout_id: int,
    request: Request,
    db: SessionDep,
    user: AuthDep,
    body: RoutineWorkoutUpdate,
):
    user_id = _require_user_id(user)
    return _get_service(db).update_routine_workout(
        routine_workout_id=routine_workout_id,
        routine_id=routine_id,
        user_id=user_id,
        sets=body.sets,
        reps=body.reps,
        order=body.order,
    )


@api_router.delete("/routines/{routine_id}/workouts/{routine_workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workout_from_routine(
    routine_id: int,
    routine_workout_id: int,
    request: Request,
    db: SessionDep,
    user: AuthDep,
):
    _get_service(db).remove_workout_from_routine(routine_workout_id, routine_id, _require_user_id(user))
