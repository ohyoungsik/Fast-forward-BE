from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.infra_repository import (
    get_latest_metrics,
    get_metrics_history,
    get_server_by_name,
)
from app.schemas.infra import MetricsHistoryPoint, MetricsLatestResponse

router = APIRouter()


def _build_latest_response(db: Session, server_name: str) -> MetricsLatestResponse:
    # server_name으로 서버를 찾고, 메트릭 타입별 최신값을 조합해 응답 객체로 변환하는 공통 헬퍼
    server = get_server_by_name(db, server_name)
    if not server:
        raise HTTPException(status_code=404, detail="서버를 찾을 수 없습니다")

    metric_map = get_latest_metrics(db, server.id)

    # metric_map에 없는 타입은 0.0으로 기본값 처리
    def val(key: str) -> float:
        return metric_map.get(key, (0.0, None))[0]

    # 수집된 메트릭 중 가장 최근 시각을 created_at으로 사용
    latest_time = max(
        (t for _, t in metric_map.values() if t is not None),
        default=None,
    )

    return MetricsLatestResponse(
        server_name=server.server_name,
        cpu_usage=val("cpu"),
        memory_usage=val("memory"),
        disk_usage=val("disk"),
        network_rx=val("network_rx"),
        network_tx=val("network_tx"),
        created_at=latest_time,
    )


@router.get("/metrics", response_model=MetricsLatestResponse)
def latest_metrics(server_name: str = Query(...), db: Session = Depends(get_db)):
    # GET /infra/metrics?server_name=bastion-server
    # 선택한 서버의 cpu / memory / disk / network 최신값 1건 반환
    return _build_latest_response(db, server_name)


@router.get("/metrics/latest", response_model=MetricsLatestResponse)
def latest_metrics_alias(server_name: str = Query(...), db: Session = Depends(get_db)):
    # GET /infra/metrics/latest — /metrics 와 동일한 응답 (경로 별칭)
    return _build_latest_response(db, server_name)


@router.get("/metrics/history", response_model=list[MetricsHistoryPoint])
def metrics_history(
    server_name: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # GET /infra/metrics/history?server_name=bastion-server&limit=20
    # 시계열 차트용: 최근 limit개 수집 시점의 cpu / memory / disk 배열 반환
    server = get_server_by_name(db, server_name)
    if not server:
        raise HTTPException(status_code=404, detail="서버를 찾을 수 없습니다")
    return get_metrics_history(db, server.id, limit)
