from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "mysql+pymysql://root:password@localhost/ai_gateway"
    llm_base_url: str = "http://localhost:11434"
    llm_model_name: str = "qwen2.5:0.5b"
    llm_num_ctx: int = 8192
    llm_timeout: int = 120
    default_rate_limit: str = "60/minute"
    log_retention_days: int = 30
    metrics_api_key: str = "change-me-in-production"
    log_level: str = "WARNING"


settings = Settings()
