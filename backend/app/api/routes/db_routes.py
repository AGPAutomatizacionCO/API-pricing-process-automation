from fastapi import APIRouter, HTTPException, Request

from app.core.access_control import (
    require_roles,
    require_user_in_access_list,
)
from app.core.audit_logger import (
    build_request_audit_data,
    write_audit_event,
)
from app.core.easy_auth import get_authenticated_user
from app.services.database_service import (
    list_databases,
    list_tables,
    test_database_connection,
)


router = APIRouter(
    prefix="/api/db",
    tags=["database"],
)


def require_authenticated_viewer(request: Request) -> dict:
    user = get_authenticated_user(request)

    access_user = require_user_in_access_list(
        user["email"]
    )

    authenticated_user = {
        **user,
        "role": access_user["role"],
    }

    require_roles(
        authenticated_user,
        ["ADMIN", "ANALYST", "VIEWER"],
    )

    return authenticated_user


def audit_access(
    *,
    request: Request,
    user: dict,
    event_type: str,
    result: str,
    resource_name: str,
    details: dict | None = None,
) -> None:
    write_audit_event(
        category="audit",
        event_type=event_type,
        result=result,
        user=user,
        request_data=build_request_audit_data(request),
        resource={
            "resource_type": "database_api",
            "resource_name": resource_name,
        },
        details=details or {},
    )


@router.get("/test")
def api_test_database_connection(request: Request):
    user = require_authenticated_viewer(request)

    try:
        data = test_database_connection()

        audit_access(
            request=request,
            user=user,
            event_type="DB_TEST_ACCESSED",
            result="SUCCESS",
            resource_name="/api/db/test",
        )

        return {
            "status": "ok",
            "data": data,
        }

    except Exception as exc:
        write_audit_event(
            category="errors",
            event_type="DB_TEST_ERROR",
            result="FAILED",
            user=user,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "database_api",
                "resource_name": "/api/db/test",
            },
            details={
                "message": str(exc),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible conectar con SQL Server: {str(exc)}",
        )


@router.get("/databases")
def api_list_databases(request: Request):
    user = require_authenticated_viewer(request)

    try:
        data = list_databases()

        audit_access(
            request=request,
            user=user,
            event_type="DB_DATABASES_ACCESSED",
            result="SUCCESS",
            resource_name="/api/db/databases",
            details={
                "count": len(data),
            },
        )

        return {
            "status": "ok",
            "count": len(data),
            "data": data,
        }

    except Exception as exc:
        write_audit_event(
            category="errors",
            event_type="DB_DATABASES_ERROR",
            result="FAILED",
            user=user,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "database_api",
                "resource_name": "/api/db/databases",
            },
            details={
                "message": str(exc),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible listar bases de datos: {str(exc)}",
        )


@router.get("/tables")
def api_list_tables(
    request: Request,
    limit: int = 50,
):
    user = require_authenticated_viewer(request)

    try:
        data = list_tables(limit=limit)

        audit_access(
            request=request,
            user=user,
            event_type="DB_TABLES_ACCESSED",
            result="SUCCESS",
            resource_name="/api/db/tables",
            details={
                "limit": limit,
                "count": len(data),
            },
        )

        return {
            "status": "ok",
            "count": len(data),
            "data": data,
        }

    except Exception as exc:
        write_audit_event(
            category="errors",
            event_type="DB_TABLES_ERROR",
            result="FAILED",
            user=user,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "database_api",
                "resource_name": "/api/db/tables",
            },
            details={
                "message": str(exc),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible listar tablas: {str(exc)}",
        )