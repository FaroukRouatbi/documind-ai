from fastapi import FastAPI
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="DocuMind AI API")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()