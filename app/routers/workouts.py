from fastapi import Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import AuthDep, AdminDep
from app.dependencies.session import SessionDep
from app.repositories.workout import WorkoutRepository
from app.models.workout import Workout
from app.utilities.flash import flash
from . import router, templates

MUSCLE_GROUPS = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Cardio", "Full Body"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]


@router.get("/workouts", response_class=HTMLResponse)
async def workouts_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    muscle_group: str = "",
    difficulty: str = "",
):
    repo = WorkoutRepository(db)
    workouts = repo.get_all_workouts(muscle_group=muscle_group, difficulty=difficulty)
    return templates.TemplateResponse(
        request=request,
        name="workouts.html",
        context={
            "user": user,
            "workouts": workouts,
            "muscle_groups": MUSCLE_GROUPS,
            "difficulties": DIFFICULTIES,
            "selected_muscle": muscle_group,
            "selected_diff": difficulty,
        },
    )


@router.get("/workouts/{workout_id}", response_class=HTMLResponse)
async def workout_detail_view(request: Request, workout_id: int, user: AuthDep, db: SessionDep):
    repo = WorkoutRepository(db)
    workout = repo.get_workout_by_id(workout_id)
    if not workout:
        flash(request, "Workout not found", "danger")
        return RedirectResponse(url=request.url_for("workouts_view"), status_code=status.HTTP_303_SEE_OTHER)
    # Also get user routines so they can add from here
    from app.repositories.workout import WorkoutRepository as WR
    routines = repo.get_user_routines(user.id)
    return templates.TemplateResponse(
        request=request,
        name="workout_detail.html",
        context={"user": user, "workout": workout, "routines": routines},
    )


# ─── Admin: Create Workout ───────────────────────────────────────────────────

@router.get("/admin/workouts/new", response_class=HTMLResponse)
async def new_workout_view(request: Request, user: AdminDep, db: SessionDep):
    return templates.TemplateResponse(
        request=request,
        name="workout_form.html",
        context={"user": user, "muscle_groups": MUSCLE_GROUPS, "difficulties": DIFFICULTIES, "workout": None},
    )


@router.post("/admin/workouts/new", response_class=HTMLResponse)
async def new_workout_action(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    name: str = Form(),
    description: str = Form(""),
    muscle_group: str = Form(),
    difficulty: str = Form(),
    duration_minutes: int = Form(30),
    equipment: str = Form("None"),
):
    repo = WorkoutRepository(db)
    workout = Workout(
        name=name,
        description=description,
        muscle_group=muscle_group,
        difficulty=difficulty,
        duration_minutes=duration_minutes,
        equipment=equipment,
    )
    try:
        repo.create_workout(workout)
        flash(request, "Workout created successfully!", "success")
    except Exception as e:
        flash(request, f"Error creating workout: {e}", "danger")
    return RedirectResponse(url=request.url_for("workouts_view"), status_code=status.HTTP_303_SEE_OTHER)


# ─── Admin: Edit Workout ────────────────────────────────────────────────────

@router.get("/admin/workouts/{workout_id}/edit", response_class=HTMLResponse)
async def edit_workout_view(request: Request, workout_id: int, user: AdminDep, db: SessionDep):
    repo = WorkoutRepository(db)
    workout = repo.get_workout_by_id(workout_id)
    if not workout:
        flash(request, "Workout not found", "danger")
        return RedirectResponse(url=request.url_for("workouts_view"), status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="workout_form.html",
        context={"user": user, "muscle_groups": MUSCLE_GROUPS, "difficulties": DIFFICULTIES, "workout": workout},
    )


@router.post("/admin/workouts/{workout_id}/edit", response_class=HTMLResponse)
async def edit_workout_action(
    request: Request,
    workout_id: int,
    user: AdminDep,
    db: SessionDep,
    name: str = Form(),
    description: str = Form(""),
    muscle_group: str = Form(),
    difficulty: str = Form(),
    duration_minutes: int = Form(30),
    equipment: str = Form("None"),
):
    repo = WorkoutRepository(db)
    try:
        repo.update_workout(workout_id, {
            "name": name,
            "description": description,
            "muscle_group": muscle_group,
            "difficulty": difficulty,
            "duration_minutes": duration_minutes,
            "equipment": equipment,
        })
        flash(request, "Workout updated!", "success")
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
    return RedirectResponse(url=request.url_for("workouts_view"), status_code=status.HTTP_303_SEE_OTHER)


# ─── Admin: Delete Workout ──────────────────────────────────────────────────

@router.post("/admin/workouts/{workout_id}/delete", response_class=HTMLResponse)
async def delete_workout_action(request: Request, workout_id: int, user: AdminDep, db: SessionDep):
    repo = WorkoutRepository(db)
    try:
        repo.delete_workout(workout_id)
        flash(request, "Workout deleted", "success")
    except Exception as e:
        flash(request, f"Error: {e}", "danger")
    return RedirectResponse(url=request.url_for("workouts_view"), status_code=status.HTTP_303_SEE_OTHER)
