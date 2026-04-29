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
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    ENV 환경변수 값을 기준으로 config/{ENV}.env 파일을 로드합니다.
    예: ENV=dev -> config/dev.env
    """
    # 먼저 OS ENV 에서 ENV 값을 읽고, 없으면 기본값 local 사용
    env = Settings().ENV
    env_file = CONFIG_DIR / f"{env}.env"
    return Settings(_env_file=str(env_file))


settings = get_settings()

