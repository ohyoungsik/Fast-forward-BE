from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_superuser
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user as create_user_service

router = APIRouter()


@router.post("", response_model=UserRead, status_code=201, summary="Create user")
async def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        return create_user_service(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[UserRead], summary="List users")
async def list_users(
    db: Session = Depends(get_db),
    _current_user=Depends(require_superuser),
) -> List[UserRead]:
    # minimal list for admin-only endpoint
    # (extend with pagination/filtering later)
    from app.models.user import User

    users = db.query(User).order_by(User.id.asc()).all()
    return [UserRead.model_validate(u) for u in users]


@router.get("/me", response_model=UserRead, summary="Get current user")
async def me(current_user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)

