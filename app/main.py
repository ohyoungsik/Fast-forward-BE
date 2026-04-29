from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # include versioned API router
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def on_startup() -> None:
        # Local 개발 편의를 위해 테이블을 자동 생성합니다.
        # 운영 환경에서는 Alembic migrations 사용을 권장합니다.
        if settings.ENV == "local" and settings.DEBUG:
            from app.db.base import Base
            from app.models import user  # noqa: F401  (import for model registration)
            from app.models import log
            Base.metadata.create_all(bind=engine)

    return app


app = create_app()

