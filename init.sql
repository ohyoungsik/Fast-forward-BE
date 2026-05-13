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
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email    ON public."user" USING btree (email);
CREATE INDEX        IF NOT EXISTS ix_user_id       ON public."user" USING btree (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_username ON public."user" USING btree (username);

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
CREATE INDEX        IF NOT EXISTS ix_refreshtoken_expires_at     ON public.refreshtoken USING btree (expires_at);
CREATE INDEX        IF NOT EXISTS ix_refreshtoken_id             ON public.refreshtoken USING btree (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_refreshtoken_refresh_token  ON public.refreshtoken USING btree (refresh_token);
CREATE INDEX        IF NOT EXISTS ix_refreshtoken_revoked        ON public.refreshtoken USING btree (revoked);
CREATE INDEX        IF NOT EXISTS ix_refreshtoken_user_id        ON public.refreshtoken USING btree (user_id);

-- =========================================
-- 3. Nginx 접근 로그 테이블  (/api/v1/logs 엔드포인트)
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
CREATE INDEX IF NOT EXISTS ix_nginx_logs_id ON nginx_logs USING btree (id);

-- =========================================
-- 4. 프로메테우스에서 가져오는 데이터를 저장하기 위한 table, indexing
-- =========================================

CREATE TABLE IF NOT EXISTS server_info (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(50) UNIQUE NOT NULL,
    server_role VARCHAR(50) NOT NULL,                        -- bastion인지, frontend, backend, db서버
    private_ip VARCHAR(50),
    public_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- 5. 서버 메트릭 통합 테이블
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
-- 1. 서버 + 메트릭 종류 + 시간 조회 

CREATE INDEX IF NOT EXISTS idx_server_metrics_server_type_time
ON server_metrics (
    server_id,
    metric_type,
    collected_at DESC
);

CREATE INDEX ON server_metrics (server_id, metric_type, collected_at DESC);

-- =========================================
-- 6. Web Application 로그 통합 테이블
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

CREATE INDEX IF NOT EXISTS idx_app_logs_collected_at ON app_logs (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_app_logs_server_type  ON app_logs (server_name, log_type);