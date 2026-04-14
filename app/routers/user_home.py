from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(request: Request, user: AuthDep, db: SessionDep):
    return RedirectResponse(url=request.url_for("workouts_view"), status_code=status.HTTP_303_SEE_OTHER)
