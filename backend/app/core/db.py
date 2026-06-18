import pyodbc

from app.core.config import get_settings


def build_connection_string() -> str:
    settings = get_settings()

    if settings.sql_trusted_connection:
        return (
            f"DRIVER={{{settings.sql_driver}}};"
            f"SERVER={settings.sql_server};"
            f"DATABASE={settings.sql_database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

    return (
        f"DRIVER={{{settings.sql_driver}}};"
        f"SERVER={settings.sql_server};"
        f"DATABASE={settings.sql_database};"
        f"UID={settings.sql_username};"
        f"PWD={settings.sql_password};"
        "TrustServerCertificate=yes;"
    )


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(
        build_connection_string(),
        timeout=10,
    )