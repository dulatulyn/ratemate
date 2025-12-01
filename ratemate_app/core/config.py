from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    PROJECT_NAME: str = "RateMate"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_CONTAINER: str | None = None
    ADMIN_PANEL_KEY: str | None = None
    ADMIN_BASIC_USERNAME: str | None = None
    ADMIN_BASIC_PASSWORD: str | None = None

settings = Settings()