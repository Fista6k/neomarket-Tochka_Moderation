from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


ERROR_CODES_BY_STATUS = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
    502: "B2B_BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}

ERROR_CODES_BY_MESSAGE = {
    "Admin privileges required": "ADMIN_REQUIRED",
    "Blocking reason not found": "BLOCKING_REASON_NOT_FOUND",
    "B2B moderation events endpoint is unavailable": "B2B_EVENTS_UNAVAILABLE",
    "Code already exists": "BLOCKING_REASON_CODE_EXISTS",
    "Duplicate event": "DUPLICATE_EVENT",
    "Email already exists": "EMAIL_ALREADY_EXISTS",
    "Inactive blocking reason": "INACTIVE_BLOCKING_REASON",
    "Invalid authorization header": "INVALID_AUTHORIZATION_HEADER",
    "Invalid blocking reason": "INVALID_BLOCKING_REASON",
    "Invalid credentials": "INVALID_CREDENTIALS",
    "Invalid or expired token": "INVALID_OR_EXPIRED_TOKEN",
    "Invalid refresh token": "INVALID_REFRESH_TOKEN",
    "Invalid service key": "INVALID_SERVICE_KEY",
    "Invalid token payload": "INVALID_TOKEN_PAYLOAD",
    "Moderator not found": "MODERATOR_NOT_FOUND",
    "Not authenticated": "NOT_AUTHENTICATED",
    "Ticket belongs to another moderator": "TICKET_BELONGS_TO_ANOTHER_MODERATOR",
    "Ticket is not in review": "TICKET_NOT_IN_REVIEW",
    "Ticket not found": "TICKET_NOT_FOUND",
    "Unknown event type": "UNKNOWN_EVENT_TYPE",
    "User inactive": "USER_INACTIVE",
    "User not found": "USER_NOT_FOUND",
    "User not found or inactive": "USER_NOT_FOUND_OR_INACTIVE",
}


def register_error_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                status_code=exc.status_code,
                detail=exc.detail,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
                "details": None,
            },
        )


def _error_payload(status_code: int, detail: Any) -> dict[str, Any]:
    if isinstance(detail, dict):
        code = detail.get("code") or ERROR_CODES_BY_STATUS.get(status_code, "ERROR")
        message = detail.get("message") or str(detail)
        details = detail.get("details")
        return {"code": code, "message": message, "details": details}

    message = str(detail) if detail else ERROR_CODES_BY_STATUS.get(status_code, "Error")
    code = ERROR_CODES_BY_MESSAGE.get(message) or ERROR_CODES_BY_STATUS.get(
        status_code,
        "ERROR",
    )
    return {"code": code, "message": message, "details": None}
