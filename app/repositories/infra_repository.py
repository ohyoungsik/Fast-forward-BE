from collections import defaultdict

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.log import Log
from app.models.server_info import ServerInfo
from app.models.server_metrics import ServerMetrics


def get_all_servers(db: Session) -> list[ServerInfo]:
    # server_info 테이블의 모든 서버를 id 오름차순으로 반환
    return db.query(ServerInfo).order_by(ServerInfo.id).all()


def get_server_by_name(db: Session, server_name: str) -> ServerInfo | None:
    # server_name으로 단일 서버 조회. 없으면 None 반환
    return db.query(ServerInfo).filter(ServerInfo.server_name == server_name).order_by(ServerInfo.id.desc()).first()


def get_latest_metrics(db: Session, server_id: int) -> dict[str, tuple[float, object]]:
    # 메트릭 타입별(cpu, memory, disk, network_rx, network_tx) 가장 최근 수집값 1건씩 조회
    # 서브쿼리로 각 metric_type의 max(collected_at)을 구한 뒤 JOIN해서 해당 행을 가져옴
    subq = (
        db.query(
            ServerMetrics.metric_type,
            func.max(ServerMetrics.collected_at).label("max_at"),
        )
        .filter(ServerMetrics.server_id == server_id)
        .group_by(ServerMetrics.metric_type)
        .subquery()
    )
    rows = (
        db.query(ServerMetrics)
        .join(
            subq,
            (ServerMetrics.metric_type == subq.c.metric_type)
            & (ServerMetrics.collected_at == subq.c.max_at),
        )
        .filter(ServerMetrics.server_id == server_id)
        .all()
    )
    # { "cpu": (25.4, datetime), "memory": (61.3, datetime), ... } 형태로 반환
    return {r.metric_type: (r.metric_value, r.collected_at) for r in rows}


def get_metrics_history(db: Session, server_id: int, limit: int = 20) -> list[dict]:
    # cpu / memory / disk 최근 N개 시계열 데이터를 수집 시각 기준으로 정렬해 반환
    # 3개 metric_type을 한 번에 조회하므로 limit * 3 행을 가져온 뒤 collected_at 기준으로 묶음
    rows = (
        db.query(ServerMetrics)
        .filter(
            ServerMetrics.server_id == server_id,
            ServerMetrics.metric_type.in_(["cpu", "memory", "disk"]),
        )
        .order_by(desc(ServerMetrics.collected_at))
        .limit(limit * 3)
        .all()
    )

    # 같은 collected_at에 수집된 cpu / memory / disk를 하나의 시점으로 묶음
    grouped: dict = defaultdict(dict)
    for r in rows:
        grouped[r.collected_at][r.metric_type] = r.metric_value

    result = []
    for ts in sorted(grouped.keys()):
        vals = grouped[ts]
        result.append(
            {
                "time": ts.strftime("%H:%M:%S") if ts else "",
                "cpu": vals.get("cpu", 0.0),
                "memory": vals.get("memory", 0.0),
                "disk": vals.get("disk", 0.0),
            }
        )
    # 오래된 데이터부터 정렬된 상태에서 마지막 limit개만 반환 (차트용 최신 N개)
    return result[-limit:]


def get_security_logs(db: Session, server_name: str | None, keyword: str | None) -> list[Log]:
    # nginx_logs 테이블은 nginx-fe-server 전용으로 간주
    # 다른 서버가 선택되면 빈 리스트 반환
    if server_name and server_name != "nginx-fe-server":
        return []

    query = db.query(Log)

    # keyword가 있으면 client_ip, request_path, status_code에 부분 일치 검색
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            Log.client_ip.ilike(kw)
            | Log.request_path.ilike(kw)
            | Log.status_code.ilike(kw)
        )
    return query.order_by(desc(Log.create_time)).limit(100).all()
