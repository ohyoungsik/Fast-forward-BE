from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# fluent-bit가 전송하는 hostname(ip-172-16-xx-xx) → 사람이 읽기 쉬운 서버명 변환
_IP_SUFFIX_TO_SERVER: dict[str, str] = {
    "172-16-10-50": "public-bastion",
    "172-16-20-10": "nginx-fe-server",
    "172-16-20-20": "fastapi-be-server",
    "172-16-20-30": "postgre-db-server",
}

def resolve_server_name(raw: str | None) -> str | None:
    """fluent-bit hostname(예: 'ip-172-16-20-10')을 서버명으로 변환.

    매핑 테이블에 없으면 원본 값을 그대로 반환.
    """
    if not raw:
        return raw
    for suffix, name in _IP_SUFFIX_TO_SERVER.items():
        if suffix in raw:
            return name
    return raw

