from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    erp_service_url: str = "http://erp-service:8001"
    database_url: str = "postgresql+asyncpg://erp_user:erp_pass@postgres:5432/erp_db"
    port: int = 8002
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url_asyncpg(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()
