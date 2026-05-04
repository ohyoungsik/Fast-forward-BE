🚀 FastAPI Backend Project Template (Production Ready)

## 📌 프로젝트 개요

이 프로젝트는 **FastAPI 기반의 확장 가능한 백엔드 아키텍처**를 목표로 합니다.  
환경 분리(local/dev/prod), 모듈화 구조, 유지보수성을 고려한 설계를 적용합니다.

---

## 🧱 프로젝트 구조

```text
app/
├── api/                # 라우터 계층 (엔드포인트)
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   └── health.py
│   │   └── router.py
│   └── deps.py (TODO)

├── core/               # 핵심 설정 및 공통 기능
│   ├── config.py       # 환경 변수 관리
│   ├── security.py     # 인증/인가
│   └── logging.py

├── db/                 # DB 관련
│   ├── session.py      # DB 연결
│   ├── base.py         # Base 모델
│   └── init_db.py

├── models/             # ORM 모델
│   └── user.py

├── schemas/            # Pydantic 스키마
│   └── user.py

├── services/           # 비즈니스 로직
│   └── user_service.py

├── repositories/       # DB 접근 계층
│   └── user_repository.py

├── utils/              # 공통 유틸
│   └── common.py

├── main.py             # FastAPI entrypoint

config/
├── local.env
├── dev.env
├── prod.env

scripts/
├── start.sh
├── migrate.sh

tests/
├── test_user.py

Dockerfile
docker-compose.yml
requirements.txt
README.md
```

---

## 🌍 환경 분리 전략

### 🔹 환경 종류

- **local** → 개발자 로컬 환경  
- **dev** → 테스트 서버  
- **prod** → 운영 환경

### 🔹 환경 변수 구조

```text
config/
├── local.env
├── dev.env
├── prod.env
```

예시는 다음과 같습니다.

```env
# local.env
ENV=local
DEBUG=true
DB_URL=postgresql://user:pass@localhost:5432/app_db
```

```env
# dev.env
ENV=dev
DEBUG=false
DB_URL=postgresql://user:pass@dev-db:5432/app_db
```

```env
# prod.env
ENV=prod
DEBUG=false
DB_URL=postgresql://user:pass@prod-db:5432/app_db
```

---

## ⚙️ config.py (핵심)

`ENV` 값에 따라 `config/{ENV}.env`를 자동으로 로드합니다.

```python
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


class Settings(BaseSettings):
    ENV: Literal["local", "dev", "prod"] = "local"
    DEBUG: bool = True
    DB_URL: str = "postgresql://user:pass@localhost:5432/app_db"
    PROJECT_NAME: str = "Fast-Forward Backend"
    API_V1_STR: str = "/api/v1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES_REFRESH: int = 60 * 24 * 7
    SECRET_KEY: str = "fast-forward"
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    env = Settings().ENV
    env_file = CONFIG_DIR / f"{env}.env"
    return Settings(_env_file=str(env_file))


settings = get_settings()
```

---

## 🧠 아키텍처 흐름

```text
API → Service → Repository → DB
```

- **API**: 요청/응답 처리  
- **Service**: 비즈니스 로직  
- **Repository**: DB 접근  
- **Model**: 테이블 구조

---

## 🔐 인증 구조 (추천)

- JWT 기반 인증  
- Access Token + Refresh Token  
- Redis (선택) → 토큰 관리

(현재 코드는 JWT 토큰 생성/검증의 최소 골격만 포함하고 있으며, 실제 비즈니스 로직/Redis 연동은 확장 포인트로 남겨두었습니다.)

---

## 📦 실행 방법

### 1️⃣ 의존성 설치

```bash
pip install -r requirements.txt
```

### 2️⃣ 로컬 실행

```bash
export ENV=local  # Windows PowerShell: $Env:ENV = "local"
uvicorn app.main:app --reload
```

또는 스크립트 사용:

```bash
chmod +x scripts/start.sh
ENV=local ./scripts/start.sh
```

### 3️⃣ Docker 실행

```bash
docker-compose up --build
```

---

## 🔐 JWT 인증 API (Backend)

Base URL: `http://localhost:8000/api/v1`

### 엔드포인트

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

### DB 테이블 생성 방법

- **local + DEBUG=true** 인 경우 서버 시작 시 자동으로 테이블을 생성합니다. (`app/main.py` 참고)
- 이미 기존 DB/볼륨이 있고 스키마가 달라 충돌한다면, 로컬 개발에서는 **DB를 비우고 다시 생성**하세요.
  - Docker 사용 시: `docker-compose down -v` 후 `docker-compose up --build`

### Postman 테스트 예시

#### 1) 회원가입

`POST /auth/register`  
Body (JSON):

```json
{
  "name": "홍길동",
  "username": "testuser",
  "password": "1234",
  "email": "test@example.com"
}
```

Response:

```json
{
  "message": "회원가입이 완료되었습니다."
}
```

#### 2) 로그인 (토큰 발급)

`POST /auth/login`  
Body (JSON):

```json
{
  "username": "testuser",
  "password": "1234"
}
```

Response:

```json
{
  "accessToken": "access-token",
  "refreshToken": "refresh-token",
  "tokenType": "bearer"
}
```

#### 3) /me (Access Token 인증)

`GET /auth/me`  
Header:

```text
Authorization: Bearer <accessToken>
```

Response:

```json
{
  "id": 1,
  "name": "홍길동",
  "username": "testuser",
  "email": "test@example.com"
}
```

#### 4) Access Token 재발급 (Refresh Token)

`POST /auth/refresh`  
Body (JSON):

```json
{
  "refreshToken": "refresh-token"
}
```

Response:

```json
{
  "accessToken": "new-access-token",
  "refreshToken": "new-refresh-token"
}
```

#### 5) 로그아웃 (Refresh Token revoke)

`POST /auth/logout`  
Header:

```text
Authorization: Bearer <accessToken>
```

Body (JSON):

```json
{
  "refreshToken": "refresh-token"
}
```

Response: `204 No Content`

### JWT 테스트 방법

- Access Token을 `Authorization: Bearer <token>` 헤더로 넘기고 `/auth/me`를 호출해 검증합니다.
- Refresh Token은 **바디**의 `refreshToken` 필드로만 전달합니다. (헤더로 전달하지 않음)

### 422 에러 디버깅 방법

- FastAPI의 `422 Unprocessable Entity`는 대부분 **요청 Body/필드명 불일치** 또는 **타입 불일치**입니다.
- 이 프로젝트의 인증 API는 프론트 요구사항에 맞춰 **camelCase** 필드를 사용합니다:
  - `accessToken`, `refreshToken`, `tokenType`
  - Request도 `refreshToken`처럼 정확히 맞춰야 합니다.
- 응답의 `detail`에 어떤 필드가 누락/오류인지 나오므로 Postman에서 **Response Body**를 먼저 확인하세요.

---

## 🧪 테스트

```bash
pytest
```

---

## 📊 로깅 & 모니터링

- **Logging** → JSON 구조 (`python-json-logger` 사용)  
- 추후 **Prometheus + Grafana** 연동 가능  
- 접근 로그 / 에러 로그 분리 구조로 확장 가능

---

## 🧩 확장 전략

- 마이크로서비스로 분리 가능  
- API 버전 관리 (`/api/v1`)  
- 이벤트 기반 구조 (Kafka, Redis 등)로 확장 가능

---

## 🔥 개발 원칙

- Fat Model ❌ → Service Layer 사용  
- 의존성 분리 (DI 적극 활용)  
- 환경 분리 필수  
- 테스트 코드 필수

---

## 💡 추천 스택

- FastAPI  
- PostgreSQL  
- SQLAlchemy  
- Alembic  
- Redis  
- Docker

---

## 🚨 주의사항

- `.env` 파일은 Git에 올리지 말 것  
- prod 환경에서 DEBUG 절대 금지  
- DB connection pooling 필수 (현재 `create_engine` 에 `pool_pre_ping` 적용)

---

## 🎯 목표

👉 “단순 CRUD가 아닌, **실제 운영 가능한 구조**”
