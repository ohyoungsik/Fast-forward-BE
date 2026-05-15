-- =========================================
-- 1. 사용자 계정 테이블
-- =========================================

CREATE TABLE IF NOT EXISTS public."user" (
    id SERIAL NOT NULL,
    name VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    is_active BOOL DEFAULT TRUE,
    is_superuser BOOL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT user_pkey PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email
ON public."user" USING btree (email);

CREATE INDEX IF NOT EXISTS ix_user_id
ON public."user" USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_username
ON public."user" USING btree (username);


-- =========================================
-- 2. JWT 리프레시 토큰 테이블
-- =========================================

CREATE TABLE IF NOT EXISTS public.refreshtoken (
    id SERIAL NOT NULL,
    user_id INT NOT NULL,
    refresh_token VARCHAR NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOL NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT refreshtoken_pkey PRIMARY KEY (id),
    CONSTRAINT refreshtoken_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public."user"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_refreshtoken_expires_at
ON public.refreshtoken USING btree (expires_at);

CREATE INDEX IF NOT EXISTS ix_refreshtoken_id
ON public.refreshtoken USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_refreshtoken_refresh_token
ON public.refreshtoken USING btree (refresh_token);

CREATE INDEX IF NOT EXISTS ix_refreshtoken_revoked
ON public.refreshtoken USING btree (revoked);

CREATE INDEX IF NOT EXISTS ix_refreshtoken_user_id
ON public.refreshtoken USING btree (user_id);


-- =========================================
-- 3. Nginx 접근 로그 테이블
-- /api/v1/logs 엔드포인트
-- =========================================

CREATE TABLE IF NOT EXISTS nginx_logs (
    id SERIAL NOT NULL,
    client_ip VARCHAR,
    method VARCHAR,
    request_path VARCHAR,
    status_code VARCHAR,
    create_time TIMESTAMP,
    CONSTRAINT nginx_logs_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_nginx_logs_id
ON nginx_logs USING btree (id);


-- =========================================
-- 4. 서버 기본 정보 테이블
-- Prometheus 메트릭 및 로그 서버 매핑용
-- =========================================

CREATE TABLE IF NOT EXISTS server_info (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(50) UNIQUE NOT NULL,
    server_role VARCHAR(50) NOT NULL,
    private_ip VARCHAR(50),
    public_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- 4-1. 서버 기본 정보 초기 데이터
-- public_ip은 생성 시 변경 필요
-- =========================================

INSERT INTO public.server_info
(server_name, server_role, private_ip, public_ip, created_at)
VALUES
('public-bastion', 'bastion', '172.16.10.50', '43.201.250.192', NOW()),
('nginx-fe-server', 'frontend', '172.16.20.10', NULL, NOW()),
('fastapi-be-server', 'backend', '172.16.20.20', NULL, NOW()),
('postgre-db-server', 'database', '172.16.20.30', NULL, NOW())
ON CONFLICT (server_name) DO UPDATE SET
    server_role = EXCLUDED.server_role,
    private_ip = EXCLUDED.private_ip,
    public_ip = EXCLUDED.public_ip;


-- =========================================
-- 5. 서버 메트릭 통합 테이블
-- CPU / Memory / Disk / Network 등
-- =========================================

CREATE TABLE IF NOT EXISTS server_metrics (
    id BIGSERIAL PRIMARY KEY,

    -- 어떤 서버인지
    server_id INT NOT NULL,

    -- cpu / memory / disk / network_rx / network_tx
    metric_type VARCHAR(30) NOT NULL,

    -- 메트릭 값
    metric_value DOUBLE PRECISION NOT NULL,

    -- %, bytes, kbps 등
    unit VARCHAR(20),

    -- 수집 시간
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_server_metrics_server
        FOREIGN KEY (server_id)
        REFERENCES server_info(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_server_metrics_server_type_time
ON server_metrics (
    server_id,
    metric_type,
    collected_at DESC
);


-- =========================================
-- 6. Web Application 로그 통합 테이블
-- nginx_access / nginx_error / fastapi_error 등
-- =========================================

CREATE TABLE IF NOT EXISTS app_logs (
    id BIGSERIAL PRIMARY KEY,

    -- nginx-fe-server, fastapi-be-server 등
    server_name VARCHAR(50),

    -- nginx_access / nginx_error / fastapi_error
    log_type VARCHAR(30) NOT NULL,

    -- INFO / WARN / ERROR / CRITICAL
    level VARCHAR(10) NOT NULL,

    client_ip VARCHAR(50),
    method VARCHAR(10),
    path TEXT,
    status_code VARCHAR(10),
    response_time_ms INT,
    message TEXT,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_logs_collected_at
ON app_logs (collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_logs_server_type
ON app_logs (server_name, log_type);


-- =========================================
-- 7. 접근 보안 로그 테이블
-- Linux SSH / sudo / session 인증 로그 저장
-- =========================================

CREATE TABLE IF NOT EXISTS security_access_logs (
    id BIGSERIAL PRIMARY KEY,

    -- public-bastion, nginx-fe-server, fastapi-be-server, postgre-db-server 등
    server_name VARCHAR(50),

    -- bastion / frontend / backend / database
    server_role VARCHAR(50),

    -- auth_log / ssh_auth / sudo / session
    log_type VARCHAR(30) NOT NULL,

    -- INFO / WARN / ERROR
    level VARCHAR(10) NOT NULL,

    -- 접속 또는 인증을 시도한 계정
    user_id VARCHAR(100),

    -- 접근 출발지 IP
    source_ip VARCHAR(50),

    -- ssh / sudo / session
    auth_method VARCHAR(30),

    -- success / failed / disconnected / session_opened / session_closed / sudo
    status VARCHAR(50),

    -- 실제 로그 파일 경로
    source_path TEXT,

    -- 화면 표시용 메시지
    message TEXT,

    -- 원본 로그 JSON 보관
    parsed_data JSONB,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_access_logs_collected_at
ON security_access_logs (collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_access_logs_server
ON security_access_logs (server_name, server_role);

CREATE INDEX IF NOT EXISTS idx_security_access_logs_source_ip
ON security_access_logs (source_ip);

CREATE INDEX IF NOT EXISTS idx_security_access_logs_status
ON security_access_logs (status);