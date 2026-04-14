from fastapi import Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.workout import WorkoutRepository
from app.utilities.flash import flash
from . import router, templates


# ─── List My Routines ────────────────────────────────────────────────────────

@router.get("/routines", response_class=HTMLResponse)
async def routines_view(request: Request, user: AuthDep, db: SessionDep):
    repo = WorkoutRepository(db)
    routines = repo.get_user_routines(user.id)
    routines = sorted(routines, key=lambda r: getattr(r, "created_at", None), reverse=True)
    return templates.TemplateResponse(
        request=request,
        name="routines.html",
        context={"user": user, "routines": routines},
    )


# ─── Create Routine ──────────────────────────────────────────────────────────

@router.get("/routines/new", response_class=HTMLResponse)
async def new_routine_view(request: Request, user: AuthDep, db: SessionDep):
    return templates.TemplateResponse(
        request=request,
        name="routine_form.html",
        context={"user": user, "routine": None},
    )


@router.post("/routines/new", response_class=HTMLResponse)
async def new_routine_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    name: str = Form(),
    description: str = Form(""),
):
    repo = WorkoutRepository(db)
    try:
        routine = repo.create_routine(name=name, description=description, user_id=user.id)
        flash(request, f"Routine '{routine.name}' created!", "success")
        return RedirectResponse(
            url=request.url_for("routine_detail_view", routine_id=routine.id),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
        return RedirectResponse(url=request.url_for("new_routine_view"), status_code=status.HTTP_303_SEE_OTHER)


# ─── View / Edit Routine ─────────────────────────────────────────────────────

@router.get("/routines/{routine_id}", response_class=HTMLResponse)
async def routine_detail_view(request: Request, routine_id: int, user: AuthDep, db: SessionDep):
    repo = WorkoutRepository(db)
    try:
        routine = repo.get_routine_by_id(routine_id)
        if not routine or routine.user_id != user.id:
            raise Exception("Routine not found")
    except Exception:
        flash(request, "Routine not found", "danger")
        return RedirectResponse(url=request.url_for("routines_view"), status_code=status.HTTP_303_SEE_OTHER)

    rw_with_workouts = []
    for rw in repo.get_routine_workouts(routine_id):
        workout = repo.get_workout_by_id(rw.workout_id)
        if workout:
            rw_with_workouts.append({"rw": rw, "workout": workout})

    all_workouts = repo.get_all_workouts()

    return templates.TemplateResponse(
        request=request,
        name="routine_detail.html",
        context={
            "user": user,
            "routine": routine,
            "rw_with_workouts": rw_with_workouts,
            "all_workouts": all_workouts,
        },
    )


@router.post("/routines/{routine_id}/edit", response_class=HTMLResponse)
async def edit_routine_action(
    request: Request,
    routine_id: int,
    user: AuthDep,
    db: SessionDep,
    name: str = Form(),
    description: str = Form(""),
):
    repo = WorkoutRepository(db)
    routine = repo.get_routine_by_id(routine_id)
    if not routine or routine.user_id != user.id:
        flash(request, "Not authorized", "danger")
        return RedirectResponse(url=request.url_for("routines_view"), status_code=status.HTTP_303_SEE_OTHER)
    try:
        repo.update_routine(routine_id, name=name, description=description)
        flash(request, "Routine updated!", "success")
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
    return RedirectResponse(
        url=request.url_for("routine_detail_view", routine_id=routine_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/routines/{routine_id}/delete", response_class=HTMLResponse)
async def delete_routine_action(request: Request, routine_id: int, user: AuthDep, db: SessionDep):
    repo = WorkoutRepository(db)
    routine = repo.get_routine_by_id(routine_id)
    if not routine or routine.user_id != user.id:
        flash(request, "Not authorized", "danger")
        return RedirectResponse(url=request.url_for("routines_view"), status_code=status.HTTP_303_SEE_OTHER)
    try:
        repo.delete_routine(routine_id)
        flash(request, "Routine deleted", "success")
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
    return RedirectResponse(url=request.url_for("routines_view"), status_code=status.HTTP_303_SEE_OTHER)


# ─── Add / Remove Workout from Routine ──────────────────────────────────────

@router.post("/routines/{routine_id}/add-workout", response_class=HTMLResponse)
async def add_workout_to_routine(
    request: Request,
    routine_id: int,
    user: AuthDep,
    db: SessionDep,
    workout_id: int = Form(),
    sets: int = Form(3),
    reps: int = Form(10),
    notes: str = Form(""),
):
    repo = WorkoutRepository(db)
    routine = repo.get_routine_by_id(routine_id)
    if not routine or routine.user_id != user.id:
        flash(request, "Not authorized", "danger")
        return RedirectResponse(url=request.url_for("routines_view"), status_code=status.HTTP_303_SEE_OTHER)
    try:
        repo.add_workout_to_routine(routine_id=routine_id, workout_id=workout_id, sets=sets, reps=reps, notes=notes)
        flash(request, "Workout added to routine!", "success")
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
    return RedirectResponse(
        url=request.url_for("routine_detail_view", routine_id=routine_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/routines/{routine_id}/remove/{rw_id}", response_class=HTMLResponse)
async def remove_workout_from_routine(
    request: Request,
    routine_id: int,
    rw_id: int,
    user: AuthDep,
    db: SessionDep,
):
    repo = WorkoutRepository(db)
    routine = repo.get_routine_by_id(routine_id)
    if not routine or routine.user_id != user.id:
        flash(request, "Not authorized", "danger")
        return RedirectResponse(url=request.url_for("routines_view"), status_code=status.HTTP_303_SEE_OTHER)
    try:
        repo.remove_workout_from_routine(rw_id)
        flash(request, "Workout removed from routine", "success")
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
    return RedirectResponse(
        url=request.url_for("routine_detail_view", routine_id=routine_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )
