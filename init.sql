--  프로메테우스에서 가져오는 데이터를 저장하기 위한 table, indexing

CREATE TABLE server_info (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(50) UNIQUE NOT NULL,
    server_role VARCHAR(50) NOT NULL,                        -- bastion인지, frontend, backend, db서버
    private_ip VARCHAR(50),
    public_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- 2. 서버 메트릭 통합 테이블
-- =========================================

CREATE TABLE server_metrics (
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

CREATE INDEX idx_server_metrics_server_type_time
ON server_metrics (
    server_id,
    metric_type,
    collected_at DESC
);

CREATE INDEX ON server_metrics (server_id, metric_type, collected_at DESC);