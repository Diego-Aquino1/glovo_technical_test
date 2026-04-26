from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    mcp_server_url: str = "http://mcp-server:8002/mcp"
    redis_url: str = "redis://redis:6379/0"

    agent_max_iterations: int = 10
    chat_history_ttl_seconds: int = 3600
    chat_history_max_messages: int = 20

    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "GlovoTest"

    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
