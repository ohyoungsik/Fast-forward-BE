from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.log_repository import get_log 
from app.schemas.log import LogListResponse

router = APIRouter()


@router.get("", response_model=LogListResponse, summary="Logs")
async def get_logs(db: Session = Depends(get_db)) -> dict:
    data = get_log(db)
    return {"payload": data}