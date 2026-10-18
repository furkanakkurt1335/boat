from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import RequestLoggingMiddleware
from app.routers import (
    admin,
    annotations,
    auth,
    comments,
    guidelines,
    search,
    sentences,
    treebanks,
    validation,
    wordlines,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="BoAT API",
        description="Boğaziçi University Annotation Tool — API",
        version="3.0.0",
    )

    app.add_middleware(RequestLoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api")
    app.include_router(treebanks.router, prefix="/api")
    app.include_router(sentences.router, prefix="/api")
    app.include_router(annotations.router, prefix="/api")
    app.include_router(wordlines.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(comments.router, prefix="/api")
    app.include_router(guidelines.router, prefix="/api")
    app.include_router(validation.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
