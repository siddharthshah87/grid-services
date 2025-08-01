# BaseSettings moved to the pydantic-settings package in Pydantic v2
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_name: str = Field(alias="DB_NAME")
    db_timeout: int = Field(30, alias="DB_TIMEOUT")

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "extra": "ignore",
        "env_nested_delimiter": "__",
    }

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()
