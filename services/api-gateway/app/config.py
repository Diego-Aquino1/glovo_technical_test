from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_gateway_key: str = "change-me-before-going-to-production"
    api_gateway_key_role: str = "viewer"
    orchestrator_url: str = "http://orchestrator:8003"
    proxy_timeout: float = 90.0
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
