from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.auth_schema import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/signup", response_model=RegisterResponse, summary="Register")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    auth_service.register(db, payload)
    return RegisterResponse(message="회원가입이 완료되었습니다.")


@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    return auth_service.login(db, payload, client_ip=client_ip)


@router.post("/refresh", response_model=RefreshResponse, summary="Refresh token")
async def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> RefreshResponse:
    return auth_service.refresh(db, payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout")
async def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    auth_service.logout(db, user_id=current_user.id, refresh_token=payload.refreshToken)
    return None


@router.get("/me", response_model=MeResponse, summary="Get current user")
async def me(current_user=Depends(get_current_user)) -> MeResponse:
    return auth_service.me_response(current_user)

