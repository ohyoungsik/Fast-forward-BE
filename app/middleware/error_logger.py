import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db.session import SessionLocal
from app.models.app_log import AppLog

_SKIP_PREFIXES = ("/api/v1/health", "/api/v1/logs", "/api/v1/infra", "/api/v1/servers")
_LEVEL_MAP = {"4": "WARN", "5": "ERROR"}
_executor = ThreadPoolExecutor(max_workers=3)


def _parse_detail(body: bytes, method: str, path: str, status: int) -> str:
    # response body JSON에서 detail 필드를 꺼내 읽기 쉬운 메시지로 변환
    try:
        data = json.loads(body)
        detail = data.get("detail", "")
        if isinstance(detail, list):
            # FastAPI Pydantic validation error: [{"loc": [...], "msg": "...", "type": "..."}]
            parts = []
            for e in detail:
                loc = " → ".join(str(x) for x in e.get("loc", []))
                msg = e.get("msg", "")
                parts.append(f"{loc}: {msg}" if loc else msg)
            detail_str = " | ".join(parts)
        else:
            detail_str = str(detail)
    except Exception:
        detail_str = ""

    base = f"{method} {path} → {status}"
    return f"{base} | {detail_str}" if detail_str else base


def _write_log_sync(server_name, log_type, level, client_ip, method, path, status_code, elapsed_ms, message):
    db = SessionLocal()
    try:
        db.add(AppLog(
            server_name=server_name,
            log_type=log_type,
            level=level,
            client_ip=client_ip,
            method=method,
            path=path,
            status_code=str(status_code),
            response_time_ms=elapsed_ms,
            message=message,
            collected_at=datetime.now(KST).replace(tzinfo=None),
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


class ErrorLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        path = request.url.path
        status = response.status_code

        if status >= 400 and not any(path.startswith(p) for p in _SKIP_PREFIXES):
            # body를 읽어서 에러 상세 메시지 추출 후 동일한 body로 Response 재조립
            body = b"".join([chunk async for chunk in response.body_iterator])
            message = _parse_detail(body, request.method, path, status)
            level = _LEVEL_MAP.get(str(status)[:1], "ERROR")
            client_ip = request.client.host if request.client else ""

            loop = asyncio.get_event_loop()
            loop.run_in_executor(
                _executor,
                _write_log_sync,
                "fastapi-be-server",
                "fastapi_error",
                level,
                client_ip,
                request.method,
                path,
                status,
                elapsed_ms,
                message,
            )

            # body를 소비했으므로 동일한 내용으로 Response 재조립해서 반환
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response
