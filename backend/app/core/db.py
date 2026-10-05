import pyodbc

from app.core.config import get_settings


def build_connection_string() -> str:
    settings = get_settings()

    if settings.sql_auth_mode == "msi":
        # Sin contrasena: ODBC Driver 18 pide el token a la Managed Identity. Certificado validado.
        uid = f"UID={settings.sql_msi_client_id};" if settings.sql_msi_client_id else ""
        return (
            f"DRIVER={{{settings.sql_driver}}};"
            f"SERVER={settings.sql_server};"
            f"DATABASE={settings.sql_database};"
            "Authentication=ActiveDirectoryMsi;"
            f"{uid}"
            "Encrypt=yes;TrustServerCertificate=no;"
        )

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