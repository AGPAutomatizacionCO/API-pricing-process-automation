from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "AGP Pricing Process API"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    sql_server: str = ""
    sql_database: str = ""
    sql_driver: str = "ODBC Driver 17 for SQL Server"
    sql_trusted_connection: bool = True
    sql_username: str | None = None
    sql_password: str | None = None

    frontend_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    access_policy_enabled: bool = True
    admin_users: str = ""
    analyst_users: str = ""
    viewer_users: str = ""

    entra_tenant_id: str = ""
    entra_frontend_client_id: str = ""
    entra_issuer: str = ""

    session_cookie_name: str = "pricing_session"
    session_secret_key: str = "CHANGE_ME"
    session_expire_minutes: int = 480
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_frontend_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]

    def get_entra_issuer(self) -> str:
        if self.entra_issuer:
            return self.entra_issuer

        if not self.entra_tenant_id:
            return ""

        return f"https://login.microsoftonline.com/{self.entra_tenant_id}/v2.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()