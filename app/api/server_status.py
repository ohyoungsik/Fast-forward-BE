import asyncio
import logging
import subprocess
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/server-status")
async def server_status_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected: %s", websocket.client)

    try:
        while True:
            ps_result = subprocess.check_output(
                [
                    "/usr/bin/ps",
                    "-eo",
                    "pid,user,%cpu,%mem,comm",
                    "--sort=-%cpu",
                ],
                text=True
            )

            lines = ps_result.strip().split("\n")
            result = "\n".join(lines[:20])

            await websocket.send_json({
                "type": "process_status",
                "data": result
            })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", websocket.client)

    except Exception as e:
        logger.error(
            "WebSocket error (client=%s): %s",
            websocket.client,
            e,
            exc_info=True
        )
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            await websocket.close()
        except Exception as close_err:
            logger.warning(
                "WebSocket 종료 중 추가 에러 (client=%s): %s",
                websocket.client,
                close_err
            )