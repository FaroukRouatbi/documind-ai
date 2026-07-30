from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.core.config import API_V1_PREFIX

router = APIRouter(prefix=API_V1_PREFIX, tags=["auth"])

@router.get("/whoami", summary="Get current authenticated user")
async def whoami(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user's ID and tenant ID, decoded from their Cognito ID token."""
    return current_user