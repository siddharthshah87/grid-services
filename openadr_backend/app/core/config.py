# BaseSettings moved to the pydantic-settings package in Pydantic v2
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_user: str
    db_password: str
    db_name: str
    admin_username: str | None = None
    admin_password_hash: str | None = None
    jwt_secret: str | None = None
    access_token_expire_minutes: int = 60

    # accept *either* DB_ or POSTGRES_ so nothing explodes while you migrate
    model_config = {
        "env_prefix": "",                         # read raw names
        "case_sensitive": False,
        "extra": "ignore",                        # ignore stray vars
        "env_nested_delimiter": "__",
    }

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:5432/{self.db_name}"
        )

settings = Settings()
