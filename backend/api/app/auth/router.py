from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter(prefix="/v1", tags=["auth"])

@router.get("/whoami")
async def whoami(current_user: dict = Depends(get_current_user)):
    return current_user