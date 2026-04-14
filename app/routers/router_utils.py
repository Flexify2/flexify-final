"""Shared utilities for router functions."""

from functools import lru_cache

from fastapi import HTTPException, status

from app.config import get_settings
from app.dependencies.auth import AuthDep
from app.services.exercise_search_service import ExerciseSearchService


@lru_cache
def get_search_service() -> ExerciseSearchService:
    """Get the exercise search service instance."""
    settings = get_settings()
    return ExerciseSearchService(
        api_key=settings.ascend_rapidapi_key,
        host=settings.ascend_rapidapi_host,
        base_url=f"https://{settings.ascend_rapidapi_host}",
    )


def require_user_id(user: AuthDep) -> int:
    """Extract and validate user ID from auth dependency.
    
    Raises HTTPException if user is not authenticated.
    """
    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user.id
