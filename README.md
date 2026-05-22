# Fast-Forward Backend

FastAPI 기반의 **인프라 모니터링 및 로그 수집 백엔드 시스템**입니다.  
서버 메트릭, Nginx 접근/에러 로그, 보안 로그(SSH/sudo), 애플리케이션 로그를 중앙화된 대시보드에서 관리합니다.

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| 프레임워크 | FastAPI 0.115.0, Uvicorn 0.31.0 |
| 데이터베이스 | PostgreSQL 16, SQLAlchemy 2.0, asyncpg 0.30 |
| 인증 | JWT (python-jose), bcrypt (passlib) |
| 스키마 검증 | Pydantic 2.9 |
| 로깅 | python-json-logger |
| 마이그레이션 | Alembic |
| 컨테이너 | Docker, docker-compose |
| 테스트 | pytest |

---

## 프로젝트 구조

```text
fast-forward-BE/
├── app/
│   ├── main.py                         # FastAPI 진입점
│   ├── api/
│   │   ├── deps.py                     # 의존성 주입 (get_current_user, require_superuser)
│   │   ├── kill.py                     # CPU 부하 테스트 API
│   │   ├── server_status.py            # WebSocket 실시간 프로세스 모니터링
│   │   └── v1/
│   │       ├── router.py               # 전체 라우터 통합
│   │       └── endpoints/
│   │           ├── auth.py             # 회원가입, 로그인, 토큰 관리
│   │           ├── user.py             # 사용자 생성 및 조회
│   │           ├── health.py           # 헬스체크
│   │           ├── servers.py          # 서버 목록 조회
│   │           ├── infra.py            # 인프라 메트릭 조회
│   │           ├── log.py              # Nginx 로그 수집 및 조회
│   │           ├── security.py         # SSH/sudo 보안 로그 수집 및 조회
│   │           └── webapp_logs.py      # FastAPI 애플리케이션 로그 조회
│   ├── core/
│   │   ├── config.py                   # 환경 변수 관리
│   │   ├── security.py                 # JWT 토큰 생성/검증
│   │   └── logging.py                  # JSON 로깅 설정
│   ├── db/
│   │   ├── base.py                     # SQLAlchemy Base 클래스
│   │   └── session.py                  # DB 연결 및 세션 관리
│   ├── models/                         # ORM 모델
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   ├── server_info.py
│   │   ├── server_metrics.py
│   │   ├── log.py                      # Nginx 로그
│   │   ├── security_access_log.py      # SSH/sudo 보안 로그
│   │   └── app_log.py                  # 애플리케이션 로그
│   ├── schemas/                        # Pydantic 요청/응답 스키마
│   │   ├── auth_schema.py
│   │   ├── user.py
│   │   ├── infra.py
│   │   └── log.py
│   ├── services/
│   │   ├── auth_service.py             # 인증 비즈니스 로직
│   │   └── user_service.py             # 사용자 관리 비즈니스 로직
│   ├── repositories/                   # DB 접근 계층
│   │   ├── user_repository.py
│   │   ├── log_repository.py
│   │   ├── security_access_log_repository.py
│   │   ├── infra_repository.py
│   │   ├── app_log_repository.py
│   │   └── refresh_token_repository.py
│   ├── utils/
│   │   └── common.py
│   ├── middleware/
│   │   └── error_logger.py             # 에러 로깅 미들웨어
│   └── metrics_collector.py            # 백그라운드 메트릭 수집
├── config/
│   ├── local.env
│   ├── dev.env
│   └── prod.env
├── scripts/
│   └── kill_cpu.sh                     # CPU 부하 테스트 스크립트
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 아키텍처

```text
Client / Fluent-bit
       ↓
  API Endpoints
       ↓
    Service
       ↓
  Repository
       ↓
SQLAlchemy ORM
       ↓
  PostgreSQL
```

---

## 환경 설정

`ENV` 환경 변수에 따라 `config/{ENV}.env` 파일을 자동으로 로드합니다.

```text
config/
├── local.env   # 로컬 개발 (DEBUG=true, 자동 테이블 생성)
├── dev.env     # 개발 서버
└── prod.env    # 운영 환경
```

```env
# local.env 예시
ENV=local
DEBUG=true
DB_URL=postgresql+asyncpg://user:pass@localhost:5432/app_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

---

## 실행 방법

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 로컬 실행

```bash
# Linux/macOS
ENV=local uvicorn app.main:app --reload

# Windows PowerShell
$env:ENV = "local"; uvicorn app.main:app --reload
```

> `ENV=local` + `DEBUG=true` 이면 서버 시작 시 테이블을 자동으로 생성합니다.

### Docker 실행

```bash
docker-compose up --build
```

docker-compose는 FastAPI 서버(`8000`)와 PostgreSQL(`5432`)를 함께 실행합니다.

```bash
# DB 볼륨 초기화가 필요한 경우
docker-compose down -v && docker-compose up --build
```

---

## API 엔드포인트

**Base URL:** `http://localhost:8000/api/v1`  
**Swagger UI:** `http://localhost:8000/docs`

### 인증 (`/auth`)

| Method | Path | 설명 | 인증 필요 |
|--------|------|------|-----------|
| POST | `/auth/signup` | 회원가입 | - |
| POST | `/auth/login` | 로그인 (Access/Refresh Token 발급) | - |
| POST | `/auth/refresh` | Access Token 재발급 (Token Rotation) | - |
| POST | `/auth/logout` | 로그아웃 (Refresh Token 폐기) | Bearer |
| GET | `/auth/me` | 현재 로그인 사용자 정보 | Bearer |

### 사용자 (`/users`)

| Method | Path | 설명 | 인증 필요 |
|--------|------|------|-----------|
| POST | `/users` | 사용자 생성 | - |
| GET | `/users` | 전체 사용자 목록 조회 | 슈퍼유저 |
| GET | `/users/me` | 현재 사용자 정보 | Bearer |

### 서버 (`/servers`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/servers` | 모니터링 대상 서버 목록 |

### 인프라 메트릭 (`/infra`)

| Method | Path | Query Params | 설명 |
|--------|------|--------------|------|
| GET | `/infra/metrics` | `server_name` | 특정 서버의 최신 메트릭 |
| GET | `/infra/metrics/latest` | `server_name` | 최신 메트릭 (위와 동일) |
| GET | `/infra/metrics/history` | `server_name`, `limit=20` | 시계열 메트릭 (차트용) |

### Nginx 로그 (`/logs`)

| Method | Path | Query Params | 설명 |
|--------|------|--------------|------|
| GET | `/logs` | - | 전체 로그 조회 |
| GET | `/logs/nginx` | `log_type`, `keyword`, `limit=100` | Nginx 로그 필터링 |
| POST | `/logs/ingest` | - | Fluent-bit → Nginx 로그 배치 수신 (204) |

### 웹앱 로그 (`/logs/webapp`)

| Method | Path | Query Params | 설명 |
|--------|------|--------------|------|
| GET | `/logs/webapp` | `log_type`, `keyword`, `limit=100` | FastAPI 로그 조회 |

### 보안 로그 (`/security/logs`)

| Method | Path | Query Params | 설명 |
|--------|------|--------------|------|
| GET | `/security/logs` | `server_name`, `keyword` | Nginx 보안 로그 조회 |
| POST | `/security/logs/ingest` | - | Fluent-bit → 보안 로그 배치 수신 (204) |
| GET | `/security/logs/access` | `server_name`, `level`, `limit=100` | SSH/sudo/세션 로그 조회 |

### 기타

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/api/kill/run` | kill_cpu.sh 실행 (부하 테스트) |
| WS | `/ws/server-status` | 실시간 프로세스 상태 모니터링 |

---

## 인증 상세

### JWT 토큰 구조

- **Access Token**: 30분 만료
- **Refresh Token**: 7일 만료, DB 저장 및 Token Rotation 적용

```json
// Payload 구조
{
  "sub": "username",
  "userId": 1,
  "type": "access",
  "exp": 1234567890
}
```

### 계정 보안

- 로그인 실패 5회 시 5분간 계정 잠금 (자동 해제)

### API 예시

#### 회원가입

```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "name": "홍길동",
  "username": "testuser",
  "password": "1234",
  "email": "test@example.com"
}
```

#### 로그인

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "1234"
}
```

```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "tokenType": "bearer"
}
```

#### Token Refresh

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJ..."
}
```

> Refresh Token은 반드시 **Request Body**의 `refreshToken` 필드로 전달합니다 (헤더 불가).

#### 로그아웃

```http
POST /api/v1/auth/logout
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "refreshToken": "eyJ..."
}
```

Response: `204 No Content`

---

## 로그 수집 (Fluent-bit 연동)

Fluent-bit가 서버의 로그 파일을 읽어 HTTP Batch POST로 전송합니다.

### Nginx 로그

- 수신 엔드포인트: `POST /api/v1/logs/ingest`
- HTTP 상태코드 기반 레벨 자동 분류:
  - `2xx`, `3xx` → INFO
  - `4xx` → WARN
  - `5xx` → ERROR

### 보안 로그 (SSH / sudo)

- 수신 엔드포인트: `POST /api/v1/security/logs/ingest`
- `/var/log/auth.log` 원문을 정규식으로 파싱
- 추출 이벤트: SSH 접속 성공/실패, 세션 열기/닫기, sudo 명령 실행
- 구조화된 데이터는 JSONB 컬럼(`parsed_data`)에 저장

---

## DB 스키마

| 테이블 | 설명 |
|--------|------|
| `user` | 사용자 계정 (로그인 실패 카운터, 계정 잠금 포함) |
| `refresh_token` | JWT Refresh Token 관리 |
| `server_info` | 모니터링 대상 서버 정보 |
| `server_metrics` | CPU/메모리/디스크/네트워크 시계열 메트릭 |
| `nginx_logs` | Nginx 접근/에러 로그 |
| `security_access_logs` | SSH/sudo/세션 보안 로그 |
| `app_logs` | FastAPI 애플리케이션 로그 |

---

## 테스트

```bash
pytest
```

---

## 주의사항

- `config/*.env` 파일은 Git에 커밋하지 않습니다
- `prod` 환경에서는 반드시 `DEBUG=false`로 설정합니다
- 응답/요청 필드명은 프론트엔드 규약에 따라 **camelCase**를 사용합니다 (`accessToken`, `refreshToken`, `tokenType`)
- `422 Unprocessable Entity` 응답 시 Response Body의 `detail` 필드에서 누락/오류 필드를 확인합니다
