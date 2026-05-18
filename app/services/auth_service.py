from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.app_log import AppLog
from app.repositories import refresh_token_repository, security_access_log_repository, user_repository
from app.schemas.auth_schema import (
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.utils.common import get_password_hash, verify_password


def _add_auth_log(db: Session, *, message: str, level: str = "INFO", path: str, status_code: str) -> None:
    # 인증 관련 이벤트(로그인/토큰갱신/로그아웃)를 app_logs 테이블에 기록
    db.add(AppLog(
        server_name="fastapi-be-server",
        log_type="auth_login",
        level=level,
        method="POST",
        path=path,
        status_code=status_code,
        message=message,
        collected_at=datetime.now(KST),
    ))
    db.commit()


def register(db: Session, payload: RegisterRequest) -> None:
    if user_repository.get_user_by_username(db, payload.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    if user_repository.get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    password_hash = get_password_hash(payload.password)
    user_repository.create_user(
        db,
        name=payload.name,
        username=payload.username,
        email=payload.email,
        password_hash=password_hash,
    )


def _add_security_log(db: Session, *, event_type: str, username: str, client_ip: str | None, message: str, level: str = "WARN") -> None:
    security_access_log_repository.create_security_access_log(
        db,
        server_name="fastapi-be-server",
        log_type=event_type,
        level=level,
        user_id=username,
        source_ip=client_ip or "",
        auth_method="password",
        status=event_type,
        message=message,
    )


def login(db: Session, payload: LoginRequest, *, client_ip: str | None = None) -> TokenResponse:
    user = user_repository.get_user_by_username(db, payload.username)
    if user is None:
        _add_auth_log(db, level="WARN", message=f"로그인 실패 | user: {payload.username} | 존재하지 않는 유저", path="/api/v1/auth/login", status_code="401")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유저가 존재하지 않음 User not found")
    if not user.is_active:
        _add_auth_log(db, level="WARN", message=f"로그인 실패 | user: {user.username} | 비활성화 계정", path="/api/v1/auth/login", status_code="403")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    # 계정 잠금 확인
    if user.locked_until:
        now = datetime.now(KST)
        if user.locked_until > now:
            remaining = int((user.locked_until - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요.",
            )
        # 잠금 시간 경과 → 자동 해제
        user_repository.reset_login_attempts(db, user)

    if not verify_password(payload.password, user.password_hash):
        updated = user_repository.record_failed_login(db, user)
        count = updated.failed_login_count
        if count >= 5:
            _add_auth_log(db, level="ERROR", message=f"계정 잠금 | user: {user.username} | 5회 실패", path="/api/v1/auth/login", status_code="423")
            _add_security_log(db, event_type="ACCOUNT_LOCKED", username=user.username, client_ip=client_ip, message="로그인 5회 실패로 5분 잠금")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="로그인 5회 실패로 계정이 5분 잠겼습니다.",
            )
        _add_auth_log(db, level="WARN", message=f"로그인 실패 | user: {user.username} | 비밀번호 불일치 ({count}/5)", path="/api/v1/auth/login", status_code="401")
        _add_security_log(db, event_type="LOGIN_FAILED", username=user.username, client_ip=client_ip, message=f"로그인 실패 {count}/5")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_repository.reset_login_attempts(db, user)

    access_token = create_access_token(username=user.username, user_id=user.id)
    refresh_token = create_refresh_token(username=user.username, user_id=user.id)

    expires_at = datetime.now(KST) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES_REFRESH)
    refresh_token_repository.create_refresh_token(
        db,
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )

    _add_auth_log(db, message=f"로그인 성공 | user: {user.username}", path="/api/v1/auth/login", status_code="200")
    return TokenResponse(accessToken=access_token, refreshToken=refresh_token, tokenType="bearer")


def refresh(db: Session, payload: RefreshRequest) -> RefreshResponse:
    rt = refresh_token_repository.get_refresh_token(db, refresh_token=payload.refreshToken)
    if rt is None or rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if rt.expires_at <= datetime.now(KST):
        refresh_token_repository.revoke_refresh_token(db, refresh_token=payload.refreshToken)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    try:
        token_payload = decode_token(payload.refreshToken)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    username = token_payload.get("sub")
    user_id = token_payload.get("userId")
    if not username or user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = user_repository.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.username != username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # rotate: revoke old refresh token and issue a new pair
    refresh_token_repository.revoke_refresh_token(db, refresh_token=payload.refreshToken)

    new_access = create_access_token(username=user.username, user_id=user.id)
    new_refresh = create_refresh_token(username=user.username, user_id=user.id)

    expires_at = datetime.now(KST) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES_REFRESH)
    refresh_token_repository.create_refresh_token(
        db,
        user_id=user.id,
        refresh_token=new_refresh,
        expires_at=expires_at,
    )

    _add_auth_log(db, message=f"토큰 갱신 | user: {username}", path="/api/v1/auth/refresh", status_code="200")
    return RefreshResponse(accessToken=new_access, refreshToken=new_refresh)


def logout(db: Session, *, user_id: int, refresh_token: str) -> None:
    rt = refresh_token_repository.get_refresh_token(db, refresh_token=refresh_token)
    if rt is None or rt.revoked or rt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    refresh_token_repository.revoke_refresh_token(db, refresh_token=refresh_token)
    _add_auth_log(db, message=f"로그아웃 | user_id: {user_id}", path="/api/v1/auth/logout", status_code="204")


def me_response(user) -> MeResponse:
    return MeResponse(id=user.id, name=user.name, username=user.username, email=user.email)

