from app.core.db import get_connection


def test_database_connection() -> dict:
    query = """
        SELECT
            @@SERVERNAME AS server_name,
            DB_NAME() AS database_name,
            SUSER_SNAME() AS login_name,
            SYSDATETIME() AS server_datetime
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()

    return {
        "server_name": row.server_name,
        "database_name": row.database_name,
        "login_name": row.login_name,
        "server_datetime": str(row.server_datetime),
    }


def list_databases() -> list[dict]:
    query = """
        SELECT
            name,
            database_id,
            state_desc
        FROM sys.databases
        ORDER BY name
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

    return [
        {
            "name": row.name,
            "database_id": row.database_id,
            "state": row.state_desc,
        }
        for row in rows
    ]


def list_tables(limit: int = 50) -> list[dict]:
    query = """
        SELECT TOP (?)
            TABLE_SCHEMA AS table_schema,
            TABLE_NAME AS table_name,
            TABLE_TYPE AS table_type
        FROM INFORMATION_SCHEMA.TABLES
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, limit)
        rows = cursor.fetchall()

    return [
        {
            "schema": row.table_schema,
            "name": row.table_name,
            "type": row.table_type,
        }
        for row in rows
    ]