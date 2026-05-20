import subprocess
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "kill_cpu.sh"

@router.post("/api/kill/run")
def run_kill_script():
    try:
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = (result.stdout or result.stderr or "").strip()
        
        if "Killing process" in output:
            import re
            match = re.search(r"Killing process (\S+) \(PID: (\d+)\)", output)
            name = match.group(1) if match else "프로세스"
            pid  = match.group(2) if match else "?"
            return { "success": True, "message": f"{name} (PID {pid}) 종료 완료", "output": output }
        
        if "No process above" in output:
            return { "success": True, "message": "임계값 초과 프로세스 없음", "output": output }
        
        return { "success": True, "message": "실행 완료", "output": output }

    except Exception as e:
        return { "success": False, "message": str(e) }