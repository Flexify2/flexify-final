from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from . import router, templates


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(request: Request, user: AdminDep, db: SessionDep):
    from app.repositories.workout import WorkoutRepository
    repo = WorkoutRepository(db)
    workouts = repo.get_all_workouts()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"user": user, "workouts": workouts},
    )
