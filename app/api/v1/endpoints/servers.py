from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.infra_repository import get_all_servers
from app.schemas.infra import ServerItem

router = APIRouter()


@router.get("", response_model=list[ServerItem])
def list_servers(db: Session = Depends(get_db)):
    # GET /servers
    # server_info 테이블의 전체 서버 목록 반환 (프론트 드롭다운용)
    return get_all_servers(db)
