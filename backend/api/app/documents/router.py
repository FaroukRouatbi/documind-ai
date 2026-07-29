from fastapi import APIRouter
from app.core.config import API_V1_PREFIX

router = APIRouter(prefix=API_V1_PREFIX, tags=["documents"])

