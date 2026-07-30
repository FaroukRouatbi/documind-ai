from fastapi import FastAPI
from app.core.config import settings

from app.auth.router import router as auth_router
from app.documents.router import router as doc_router

from app.core.logging import configure_logging
from app.core.middleware import CorrelationIdMiddleware, RequestSizeLimitMiddleware

def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="DocuMind AI API",
                  description=(
                    "Multi-tenant RAG document Q&A platform API. "
                    "All endpoints under /v1 require a Bearer ID token issued by Cognito; "
                    "requests are automatically scoped to the authenticated user's tenant "
                    "via row-level security."
    ),
                  version="1.0.0",
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)

    @app.get("/health", summary="Health check")
    async def health():
        """Returns a simple status indicator confirming the API is running."""
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(doc_router)

    return app


app = create_app()