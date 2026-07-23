from fastapi import FastAPI
from app.core.config import settings

from app.auth.router import router as auth_router

def create_app() -> FastAPI:
    app = FastAPI(title="DocuMind AI API")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(auth_router)

    return app


app = create_app()