import os
from dotenv import load_dotenv

load_dotenv()

PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://172.16.8.200:9090/api/v1/query")
# Prometheus가 설치된 서버의 실제 IP (127.0.0.1 instance 매핑용)
PROMETHEUS_SERVER_IP: str = os.getenv("PROMETHEUS_SERVER_IP", "172.16.8.200")

DB_HOST: str = os.getenv("DB_HOST", "172.16.8.201")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_NAME: str = os.getenv("DB_NAME", "scott_db")
DB_USER: str = os.getenv("DB_USER", "scott")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "tiger")

COLLECT_INTERVAL: int = int(os.getenv("COLLECT_INTERVAL", "15"))

NETWORK_DEVICE: str = os.getenv("NETWORK_DEVICE", "ens160")

METRICS: dict = {
    "cpu": {
        "query": '100 - (avg by (instance, job) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)',
        "unit": "%",
    },
    "memory": {
        "query": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
        "unit": "%",
    },
    "disk": {
        "query": '(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100',
        "unit": "%",
    },
    "network_rx": { # 서버가 초당 얼마나 데이터를 받고 있는가
        "query": f'sum by (instance) (rate(node_network_receive_bytes_total{{device="{NETWORK_DEVICE}"}}[1m]))',
        "unit": "bytes/s",
    },
    "network_tx": { # 서버가 초당 얼마나 데이터를 보내고 있는가
        "query": f'sum by (instance) (rate(node_network_transmit_bytes_total{{device="{NETWORK_DEVICE}"}}[1m]))',
        "unit": "bytes/s",
    },
}
