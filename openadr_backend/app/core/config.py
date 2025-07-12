# BaseSettings moved to the pydantic-settings package in Pydantic v2
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_user: str
    db_password: str
    db_name: str


    model_config = {
        "env_prefix": "POSTGRES_",
        "case_sensitive": False,
    }

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:5432/{self.db_name}"
        )

settings = Settings()
