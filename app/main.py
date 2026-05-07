import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine


def create_app() -> FastAPI:
    setup_logging()

    # @asynccontextmanager
    # async def lifespan(_app: FastAPI):
    #     # FastAPI 시작 시 실행
    #     if settings.ENV == "local" and settings.DEBUG:
    #         from app.db.base import Base
    #         from app.models import user  # noqa: F401
    #         from app.models import log
    #         from app.models import refresh_token
    #         Base.metadata.create_all(bind=engine)

    #     # 메트릭 수집기 백그라운드 실행
    #     from app.metrics_collector import main as collector_main
    #     task = asyncio.create_task(collector_main())
    #     print("[FastAPI] 메트릭 수집기 백그라운드 시작")

    #     yield

    #     # FastAPI 종료 시 실행
    #     task.cancel()
    #     try:
    #         await task
    #     except asyncio.CancelledError:
    #         print("[FastAPI] 메트릭 수집기 종료")

    # app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
