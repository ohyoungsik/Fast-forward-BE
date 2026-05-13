#!/bin/bash
# FastAPI 서버 배포 셋업 스크립트
# deploy.yml에서 tar 추출 후 이 스크립트를 실행함
# 실행 위치: FastAPI 서버 (172.16.20.20)
set -e

APP_DIR="/var/www/fastapi_app"

echo "===== DEPLOY START ====="
hostname
whoami

# ── .env 파일 확인 ────────────────────────────────────────────────────────────
echo "===== MOVE ENV ====="
sudo mv /tmp/.env "$APP_DIR/.env"

echo "===== CHECK ENV FILE ====="
if [ ! -f "$APP_DIR/.env" ]; then
  echo "ERROR: $APP_DIR/.env file does not exist"
  exit 1
fi

# 주요 환경변수 값 출력 (배포 로그에서 설정 검증용)
sudo grep -E "PROMETHEUS_URL|PROMETHEUS_SERVER_IP|DB_HOST|DB_NAME|COLLECT_INTERVAL|DB_URL" "$APP_DIR/.env" || true

# ── 시스템 패키지 설치 ────────────────────────────────────────────────────────
echo "===== INSTALL SYSTEM PACKAGE ====="
sudo apt update
sudo apt install -y \
  python3-venv \
  python3-pip \
  python3.12-venv \
  postgresql-client

# ── venv 생성 및 패키지 설치 ──────────────────────────────────────────────────
# venv가 없을 때만 새로 생성 (재배포 시 불필요한 재생성 방지)
# www-data 유저로 설치해야 shebang 경로가 서버 경로로 설정됨
# root로 설치하면 shebang이 /root/...가 되어 www-data(gunicorn 실행 유저)가 실행 불가
echo "===== INSTALL PYTHON DEPENDENCIES ====="
cd "$APP_DIR"

if [ ! -d "venv" ]; then
  sudo python3 -m venv venv
fi

sudo chown -R www-data:www-data "$APP_DIR"
sudo chmod 600 "$APP_DIR/.env"

sudo -u www-data "$APP_DIR/venv/bin/python" -m pip install --upgrade pip

if [ -f "$APP_DIR/requirements.txt" ]; then
  sudo -u www-data "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
else
  echo "ERROR: requirements.txt not found"
  exit 1
fi

# requirements.txt에 포함되어 있지만 명시적으로 재확인
sudo -u www-data "$APP_DIR/venv/bin/pip" install gunicorn uvicorn

# gunicorn shebang 경로 확인
# 정상: #!/var/www/fastapi_app/venv/bin/python3
# 비정상: #!/home/runner/... (runner 경로면 서버에서 실행 불가 → 203/EXEC 오류)
echo "===== CHECK GUNICORN ====="
ls -al "$APP_DIR/venv/bin/gunicorn"
head -1 "$APP_DIR/venv/bin/gunicorn"

# ── DB 초기화 ──────────────────────────────────────────────────────────────────
echo "===== DB INIT ====="
DB_URL=$(grep "^DB_URL=" "$APP_DIR/.env" | cut -d= -f2- || true)

if [ -n "$DB_URL" ] && [ -f "$APP_DIR/init.sql" ]; then
  psql "$DB_URL" -f "$APP_DIR/init.sql"
else
  echo "DB_URL or init.sql not found. Skip DB INIT."
fi

# ── systemd 서비스 등록 ────────────────────────────────────────────────────────
echo "===== CREATE FASTAPI LOG DIR ====="
sudo mkdir -p /var/log/fastapi
sudo chown www-data:www-data /var/log/fastapi

# 레포의 scripts/fastapi.service 파일을 복사 후 CRLF 제거
# (Windows에서 편집 시 \r\n이 섞이면 systemd가 ExecStart 경로를 못 찾아 203/EXEC 오류 발생)
echo "===== CREATE FASTAPI SERVICE ====="
sudo cp "$APP_DIR/scripts/fastapi.service" /etc/systemd/system/fastapi.service
sudo sed -i 's/\r//' /etc/systemd/system/fastapi.service

echo "===== SYSTEMD RELOAD ====="
sudo systemctl daemon-reload

echo "===== ENABLE FASTAPI ====="
sudo systemctl enable fastapi.service

echo "===== RESTART FASTAPI ====="
sudo systemctl restart fastapi.service

sleep 5

# ── 배포 후 상태 확인 (|| true 로 set -e 조기 종료 방지) ─────────────────────
echo "===== FASTAPI STATUS ====="
sudo systemctl status fastapi.service --no-pager || true

echo "===== FASTAPI JOURNAL LOG ====="
sudo journalctl -u fastapi.service -n 100 --no-pager || true

echo "===== GUNICORN ERROR LOG ====="
sudo tail -n 100 /var/log/fastapi/error.log 2>/dev/null || echo "No error log yet"

echo "===== PROCESS CHECK ====="
ps -ef | grep gunicorn | grep -v grep || true

echo "===== PORT CHECK ====="
sudo ss -lntp | grep 8000 || true

# curl -v 로 응답 상세 확인 후, -f 로 실제 성공/실패 판정
echo "===== HEALTH CHECK ====="
curl -v http://127.0.0.1:8000/api/v1/health || true

curl -f http://127.0.0.1:8000/api/v1/health \
  && echo "HEALTH CHECK PASSED" \
  || { echo "HEALTH CHECK FAILED"; sudo journalctl -u fastapi.service -n 150 --no-pager; exit 1; }

echo "===== DEPLOY END ====="
