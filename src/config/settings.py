from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Rokomari Product Pipeline"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "hardpass1"
    DB_NAME: str = "rokomari_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    VENDOR_A_URL: str = "http://vendor-a:8001"
    VENDOR_B_URL: str = "http://vendor-b:8002"
    VENDOR_C_URL: str = "http://vendor-c:8003"
    VENDOR_D_URL: str = "http://vendor-d:8004"

    VENDOR_A_RATE_LIMIT: int = 10
    VENDOR_B_RATE_LIMIT: int = 5
    VENDOR_C_RATE_LIMIT: int = 20
    VENDOR_D_RATE_LIMIT: int = 8

    MAX_CONCURRENT_REQUEST: int = 50
    REQUEST_TIMEOUT: int = 30
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.75

    DATA_INPUT_PATH: str = "data/input/messy_product.json"
    DATA_OUTPUT_PATH: str = "data/output"
    LOG_PATH: str = "logs"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()