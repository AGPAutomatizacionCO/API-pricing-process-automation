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

    easy_auth_enabled: bool = True
    local_auth_enabled: bool = True
    local_auth_email: str = "miuser@agpglass.com"
    local_auth_name: str = "Usuario Local"

    sql_server: str = ""
    sql_database: str = ""
    sql_driver: str = "ODBC Driver 17 for SQL Server"
    sql_trusted_connection: bool = False
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

    admin_groups: str = ""
    analyst_groups: str = ""
    viewer_groups: str = ""

    log_level: str = "INFO"
    audit_log_enabled: bool = True

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

    def get_admin_users(self) -> set[str]:
        return self._split_csv_to_set(self.admin_users)

    def get_analyst_users(self) -> set[str]:
        return self._split_csv_to_set(self.analyst_users)

    def get_viewer_users(self) -> set[str]:
        return self._split_csv_to_set(self.viewer_users)

    @staticmethod
    def _split_csv_to_set(value: str) -> set[str]:
        return {
            item.strip().lower()
            for item in value.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()