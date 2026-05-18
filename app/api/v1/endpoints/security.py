import logging
import re

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.repositories.infra_repository import get_security_logs
from app.repositories.security_access_log_repository import (
    create_security_access_log,
    get_security_access_logs,
)
from app.schemas.infra import FluentBitRecord, SecurityAccessLogItem, SecurityLogItem
from app.utils.common import resolve_server_name

router = APIRouter()

# HTTP 상태코드 첫 자리로 로그 레벨 결정 (2xx/3xx → INFO, 4xx → WARN, 5xx → ERROR)
_LEVEL_MAP = {"2": "INFO", "3": "INFO", "4": "WARN", "5": "ERROR"}


@router.get("", response_model=list[SecurityLogItem])
def security_logs(
    server_name: str = Query(default=None),
    keyword: str = Query(default=None),
    db: Session = Depends(get_db),
):
    # GET /security/logs?server_name=nginx-fe-server&keyword=404
    # nginx_logs 테이블에서 로그를 조회한 뒤 프론트 표시용 형식으로 변환해 반환
    # keyword는 client_ip / request_path / status_code 부분 일치 검색에 사용
    logs = get_security_logs(db, server_name, keyword)
    result = []
    for log in logs:
        code = str(log.status_code or "")
        level = _LEVEL_MAP.get(code[:1], "INFO")
        # method가 있으면 "GET /path → 200" 형태, 없으면 request_path만 표시
        message = (
            f"{log.method} {log.request_path} → {log.status_code}"
            if log.method
            else log.request_path or ""
        )
        result.append(
            SecurityLogItem(
                id=log.id,
                timestamp=log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else "",
                level=level,
                ip=log.client_ip or "",
                status_code=code,
                message=message,
                service="nginx",
            )
        )
    return result


_STATUS_TO_LEVEL = {
    "failed": "WARN",
    "session_opened": "INFO",
    "session_closed": "INFO",
    "sudo": "INFO",
}


def _resolve_level(rec_status: str | None) -> str:
    return _STATUS_TO_LEVEL.get(rec_status or "", "INFO")


def _parse_auth_log(raw: str) -> dict | None:
    """auth.log 원문에서 status/user_id/source_ip/auth_method/source_path 추출.
    저장 불필요한 이벤트는 None 반환."""

    # SSH 인증 성공: Accepted publickey for ubuntu from 1.2.3.4 port 22 ssh2
    m = re.search(r"Accepted (\w+) for (\S+) from ([\d.:a-fA-F]+) port \d+", raw)
    if m:
        return {
            "status": "session_opened",
            "auth_method": m.group(1),
            "user_id": m.group(2),
            "source_ip": m.group(3),
        }

    # SSH 인증 실패: Failed password/publickey for [invalid user] ubuntu from 1.2.3.4 port 22
    m = re.search(r"Failed (\w+) for (?:invalid user )?(\S+) from ([\d.:a-fA-F]+) port \d+", raw)
    if m:
        return {
            "status": "failed",
            "auth_method": m.group(1),
            "user_id": m.group(2),
            "source_ip": m.group(3),
        }

    # SSH 세션 종료: pam_unix(sshd:session): session closed for user ubuntu
    m = re.search(r"sshd.*session closed for user (\S+)", raw)
    if m:
        return {
            "status": "session_closed",
            "user_id": m.group(1),
        }

    # sudo 실제 명령: sudo:   ubuntu : TTY=pts/1 ; PWD=... ; USER=root ; COMMAND=/usr/bin/...
    m = re.search(r"sudo:\s{1,5}(\S+)\s+:.*?COMMAND=(.+)$", raw)
    if m:
        return {
            "status": "sudo",
            "user_id": m.group(1),
            "source_path": m.group(2).strip(),
        }

    # 나머지(sshd session opened, sudo session opened/closed 등): 중복이므로 저장 안 함
    return None


def _build_message(status: str | None, user_id: str | None, source_ip: str | None,
                   auth_method: str | None, source_path: str | None) -> str | None:
    uid = user_id or "unknown"
    ip = source_ip or "-"
    method = auth_method or "-"
    if status == "session_opened":
        return f"SSH 접속 성공 — user={uid}, from={ip}, method={method}"
    if status == "session_closed":
        return f"SSH 세션 종료 — user={uid}"
    if status == "failed":
        return f"SSH 인증 실패 — user={uid}, from={ip}"
    if status == "sudo":
        return f"sudo 실행 — user={uid}, command={source_path or '-'}"
    return None


def _build_parsed_data(status: str | None, user_id: str | None, source_ip: str | None,
                       auth_method: str | None, source_path: str | None) -> dict | None:
    if status == "session_opened":
        return {"event": "ssh_login", "user_id": user_id, "source_ip": source_ip, "auth_method": auth_method}
    if status == "session_closed":
        return {"event": "ssh_logout", "user_id": user_id}
    if status == "failed":
        return {"event": "ssh_auth_failed", "user_id": user_id, "source_ip": source_ip}
    if status == "sudo":
        return {"event": "sudo_command", "user_id": user_id, "command": source_path}
    return None


@router.post("/ingest", status_code=status.HTTP_204_NO_CONTENT)
def ingest_security_logs(
    records: list[FluentBitRecord],
    db: Session = Depends(get_db),
):
    # POST /security/logs/ingest
    # fluent-bit HTTP output 플러그인에서 security_access_logs 레코드를 배치로 수신
    # auth.log 원문(rec.log)을 파싱해 user_id/source_ip/auth_method/status 추출 후 저장
    for rec in records:
        parsed = _parse_auth_log(rec.log or "")
        if parsed is None:
            continue

        final_status = parsed.get("status")
        user_id     = parsed.get("user_id")
        source_ip   = parsed.get("source_ip")
        auth_method = parsed.get("auth_method")
        source_path = parsed.get("source_path")

        data = {
            "server_name": resolve_server_name(rec.server_name),
            "server_role": rec.server_role,
            "log_type":    rec.log_type,
            "level":       _resolve_level(final_status),
            "user_id":     user_id,
            "source_ip":   source_ip,
            "auth_method": auth_method,
            "status":      final_status,
            "source_path": source_path or rec.source_path,
            "message":     _build_message(final_status, user_id, source_ip, auth_method, source_path),
            "parsed_data": _build_parsed_data(final_status, user_id, source_ip, auth_method, source_path),
        }
        try:
            create_security_access_log(db, **data)
        except Exception as e:
            logger.error("security log insert 실패: %s | data: %s", e, data)


@router.get("/access", response_model=list[SecurityAccessLogItem])
def security_access_logs(
    server_name: str = Query(default=None),
    level: str = Query(default=None),
    status: str = Query(default=None),
    keyword: str = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # GET /security/logs/access?server_name=public-bastion&level=WARN&limit=100
    # security_access_logs 테이블에서 SSH/sudo/세션 인증 로그 조회
    logs = get_security_access_logs(db, server_name, level, status, keyword, limit)
    return [
        SecurityAccessLogItem(
            id=log.id,
            server_name=log.server_name or "",
            server_role=log.server_role or "",
            log_type=log.log_type,
            level=log.level,
            user_id=log.user_id or "",
            source_ip=log.source_ip or "",
            auth_method=log.auth_method or "",
            status=log.status or "",
            source_path=log.source_path or "",
            message=log.message or "",
            collected_at=log.collected_at.strftime("%Y-%m-%d %H:%M:%S") if log.collected_at else "",
        )
        for log in logs
    ]
