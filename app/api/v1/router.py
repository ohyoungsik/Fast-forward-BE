from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, infra, log, security, servers, user

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(log.router, prefix="/logs", tags=["logs"])
api_router.include_router(servers.router, prefix="/servers", tags=["servers"])
api_router.include_router(infra.router, prefix="/infra", tags=["infra"])
api_router.include_router(security.router, prefix="/security/logs", tags=["security"])
