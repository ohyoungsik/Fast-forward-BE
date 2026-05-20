import logging
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "kill_cpu.sh"


@router.post("/api/kill/run")
def run_kill_script():
    try:
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "kill_cpu.sh 실행 실패",
                    "output": output,
                    "error": error,
                }
            )
        return {
            "success": True,
            "message": output,
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error("kill_cpu.sh 실행 실패: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))