from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.log_repository import create_nginx_log, get_log
from app.schemas.log import LogListResponse, NginxIngestRecord

router = APIRouter()


@router.get("", response_model=LogListResponse, summary="Logs")
async def get_logs(db: Session = Depends(get_db)) -> dict:
    data = get_log(db)
    return {"payload": data}


@router.post("/ingest", status_code=status.HTTP_204_NO_CONTENT)
def ingest_nginx_logs(
    records: list[NginxIngestRecord],
    db: Session = Depends(get_db),
):
    # POST /logs/ingest
    # fluent-bit HTTP output 플러그인에서 nginx access/error 로그를 배치로 수신
    #
    # fluent-bit 설정 예시:
    #   [OUTPUT]
    #       Name   http
    #       Match  nginx.*          ← nginx.access / nginx.error 둘 다 매칭
    #       Host   <BE_HOST>
    #       Port   8000
    #       URI    /api/v1/logs/ingest
    #       Format json
    #
    # 레코드에 log_type 필드로 'access' | 'error' 를 반드시 포함해야 함
    for rec in records:
        create_nginx_log(db, **rec.model_dump())