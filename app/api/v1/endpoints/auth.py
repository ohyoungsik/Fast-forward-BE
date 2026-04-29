from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.repositories.user_repository import get_user_by_email
from app.schemas.user import Token, UserLogin
from app.utils.common import verify_password

router = APIRouter()


@router.post("/login", response_model=Token, summary="User login")
async def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    access = create_access_token(subject=str(user.id))
    refresh = create_refresh_token(subject=str(user.id))
    return Token(access_token=access, refresh_token=refresh, token_type="bearer")

