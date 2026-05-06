print("[START] metrics_collector.py 시작")

import asyncio
import sys
from datetime import datetime, timezone
from typing import Optional

print("[IMPORT] 표준 라이브러리 로드 완료")

try:
    import asyncpg
    print("[IMPORT] asyncpg 로드 완료")
except ImportError as e:
    print(f"[IMPORT ERROR] asyncpg 없음: {e}")
    print("  -> pip install asyncpg 실행 필요")
    sys.exit(1)

try:
    import httpx
    print("[IMPORT] httpx 로드 완료")
except ImportError as e:
    print(f"[IMPORT ERROR] httpx 없음: {e}")
    sys.exit(1)

try:
    from app.config import (
        COLLECT_INTERVAL,
        DB_HOST,
        DB_NAME,
        DB_PASSWORD,
        DB_PORT,
        DB_USER,
        METRICS,
        PROMETHEUS_URL,
        PROMETHEUS_SERVER_IP,
    )
    print("[IMPORT] app.config 로드 완료")
except Exception as e:
    print(f"[IMPORT ERROR] app.config 로드 실패: {e}")
    sys.exit(1)

try:
    from app.logger import get_logger
    print("[IMPORT] app.logger 로드 완료")
except Exception as e:
    print(f"[IMPORT ERROR] app.logger 로드 실패: {e}")
    sys.exit(1)

logger = get_logger("metrics_collector")


async def create_db_pool() -> asyncpg.Pool:
    print(f"[DB] 연결 시도: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    try:
        pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=2,
            max_size=10,
        )
        print("[DB] 커넥션 풀 생성 완료")
        return pool
    except Exception as e:
        print(f"[DB] 연결 실패: {e}")
        sys.exit(1)


async def load_server_info(pool: asyncpg.Pool) -> dict[str, int]:
    print("[DB] server_info 조회 중...")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, private_ip, public_ip FROM server_info")

    ip_to_id: dict[str, int] = {}
    for row in rows:
        if row["private_ip"]:
            ip_to_id[row["private_ip"]] = row["id"]
        if row["public_ip"]:
            ip_to_id[row["public_ip"]] = row["id"]

    # Prometheus가 자기 자신을 127.0.0.1로 리포트할 경우 실제 IP로 매핑
    if PROMETHEUS_SERVER_IP and PROMETHEUS_SERVER_IP in ip_to_id:
        ip_to_id["127.0.0.1"] = ip_to_id[PROMETHEUS_SERVER_IP]
        print(f"[DB] 127.0.0.1 -> {PROMETHEUS_SERVER_IP} (server_id={ip_to_id[PROMETHEUS_SERVER_IP]}) 매핑 추가")

    print(f"[DB] server_info 로드 완료: {ip_to_id}")
    return ip_to_id


async def fetch_metric(
    client: httpx.AsyncClient,
    metric_name: str,
    query: str,
) -> Optional[list[dict]]:
    print(f"[Prometheus] {metric_name} 조회 중...")
    try:
        response = await client.get(PROMETHEUS_URL, params={"query": query}, timeout=10.0)
        print(f"[Prometheus] {metric_name} HTTP 상태코드: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            print(f"[Prometheus] {metric_name} 응답 비정상: {data.get('status')}")
            return None

        results = data.get("data", {}).get("result", [])
        print(f"[Prometheus] {metric_name} 결과 수: {len(results)}개")
        for r in results:
            print(f"  instance={r.get('metric', {}).get('instance')}  value={r.get('value')}")
        return results
    except Exception as e:
        print(f"[Prometheus] {metric_name} 요청 실패: {e}")
        return None


def parse_instance_ip(instance: str) -> str:
    return instance.split(":")[0]


async def collect_and_store(pool: asyncpg.Pool, ip_to_id: dict[str, int]) -> None:
    # collected_at = datetime.now(timezone.utc)
    collected_at = datetime.now(timezone.utc).replace(tzinfo=None)
    records: list[tuple] = []

    print(f"\n{'='*50}")
    print(f"[Collector] 수집 사이클 시작: {collected_at.strftime('%Y-%m-%d %H:%M:%S')}")

    async with httpx.AsyncClient() as client:
        for metric_name, meta in METRICS.items():
            results = await fetch_metric(client, metric_name, meta["query"])
            if results is None:
                continue

            for result in results:
                instance = result.get("metric", {}).get("instance", "")
                ip = parse_instance_ip(instance)
                server_id = ip_to_id.get(ip)

                if server_id is None:
                    print(f"[Collector] server_info에 없는 인스턴스: {ip}")
                    continue

                try:
                    value = float(result["value"][1])
                except (KeyError, IndexError, ValueError) as e:
                    print(f"[Collector] {metric_name} 값 파싱 실패 (instance={instance}): {e}")
                    continue

                print(f"[Collector] 저장 대상: server_id={server_id}, metric={metric_name}, value={value:.4f} {meta['unit']}")
                records.append((server_id, metric_name, value, meta["unit"], collected_at))

    print(f"[Collector] 총 {len(records)}건 INSERT 시도")

    if not records:
        print("[Collector] 저장할 데이터 없음 - INSERT 생략")
        return

    try:
        async with pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO server_metrics (server_id, metric_type, metric_value, unit, collected_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                records,
            )
        print(f"[DB] INSERT 완료: {len(records)}건")
    except Exception as e:
        print(f"[DB] INSERT 실패: {e}")


async def main() -> None:
    pool = await create_db_pool()
    ip_to_id = await load_server_info(pool)

    print(f"[Collector] 수집 시작 (주기: {COLLECT_INTERVAL}초)")

    try:
        while True:
            try:
                await collect_and_store(pool, ip_to_id)
            except Exception as e:
                print(f"[Collector] 수집 사이클 오류: {e}")
            print(f"[Collector] {COLLECT_INTERVAL}초 대기 중...")
            await asyncio.sleep(COLLECT_INTERVAL)
    finally:
        await pool.close()
        print("[DB] 커넥션 풀 종료")


if __name__ == "__main__":
    asyncio.run(main())
