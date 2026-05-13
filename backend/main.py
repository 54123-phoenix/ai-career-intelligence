"""FastAPI application entry point.

Architect-owned. Routes are registered here; business logic lives in Agent domains.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks. No business logic — only infrastructure."""
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Career Intelligence System",
        description="Multi-Agent career decision simulation platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check (no deps, always available)
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": app.version}

    # L1 routes — mounted when Agent domains deliver implementations
    # from backend.api.routes.parser import router as parser_router
    # app.include_router(parser_router, prefix="/api/v1/parser", tags=["L1 Parser"])

    from backend.api.routes.retrieval import router as retrieval_router

    app.include_router(retrieval_router, prefix="/api/v1/retrieval", tags=["L1 Retrieval"])

    # L1 Ingestion routes
    from backend.api.routes.data_ingestion import router as ingestion_router

    app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["L1 Ingestion"])

    # L2 routes
    from backend.api.routes.simulation import router as simulation_router

    app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["L2 Simulation"])

    # L3 Feedback routes
    from backend.api.routes.feedback import router as feedback_router

    app.include_router(feedback_router, prefix="/api/v1/feedback", tags=["L3 Feedback"])

    # Pipeline orchestration routes
    from backend.api.routes.pipeline import router as pipeline_router

    app.include_router(pipeline_router, prefix="/api/v1/pipeline", tags=["Pipeline"])

    # T006 Signal Layer — trace routes
    from backend.api.routes.trace import router as trace_router

    app.include_router(trace_router, prefix="/api/v1/trace", tags=["T006 Trace"])

    # T006 LTR — ranking routes
    from backend.api.routes.ranking import router as ranking_router

    app.include_router(ranking_router, prefix="/api/v1/ranking", tags=["L3 Ranking"])

    # T006 L3 — session routes
    from backend.api.routes.session import router as session_router

    app.include_router(session_router, prefix="/api/v1/session", tags=["L3 Session"])

    # T007 — career routes (split into 4 sub-files)
    from backend.api.routes.analysis import router as analysis_router
    from backend.api.routes.path import router as path_router
    from backend.api.routes.recommendation import router as recommendation_router
    from backend.api.routes.report import router as report_router

    app.include_router(analysis_router, prefix="/api/v1/career", tags=["Career"])
    app.include_router(path_router, prefix="/api/v1/career", tags=["Career"])
    app.include_router(recommendation_router, prefix="/api/v1/career", tags=["Career"])
    app.include_router(report_router, prefix="/api/v1/career", tags=["Career"])

    # Auth & User routes
    from backend.api.routes.auth import router as auth_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(auth_router, prefix="/api/v1/users", tags=["User"])

    # Chat routes
    from backend.api.routes.chat import router as chat_router

    app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])

    return app


app = create_app()
