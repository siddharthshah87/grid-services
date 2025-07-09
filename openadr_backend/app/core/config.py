from pydantic import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_user: str
    db_password: str
    db_name: str

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:5432/{self.db_name}"
        )

settings = Settings()
