from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
from app.core.logging import get_logger
import traceback

logger = get_logger("exceptions")

class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 400, detail: str = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

class DatabaseException(AppException):
    """Database operation exception"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(message, status_code=500, detail=detail)

class AuthenticationException(AppException):
    """Authentication exception"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationException(AppException):
    """Authorization exception"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)

class NotFoundException(AppException):
    """Resource not found exception"""
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)

class ValidationException(AppException):
    """Validation exception"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(message, status_code=422, detail=detail)

def add_exception_handlers(app: FastAPI):
    """Register exception handlers with FastAPI app"""

    def _sanitize_errors(errors: list) -> list:
        """
        Strip any non-JSON-serializable values (bytes, etc.) from Pydantic
        validation error dicts so JSONResponse never raises a TypeError.
        """
        safe = []
        for err in errors:
            clean = {}
            for k, v in err.items():
                if isinstance(v, bytes):
                    clean[k] = f"<bytes len={len(v)}>"
                elif isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                    clean[k] = v
                else:
                    clean[k] = str(v)
            safe.append(clean)
        return safe

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(f"AppException: {exc.message} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "detail": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation failed",
                "detail": _sanitize_errors(exc.errors()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error: {str(exc)}", exc_info=True)
        if isinstance(exc, IntegrityError):
            detail = "Database constraint violation"
        else:
            detail = "Database operation failed"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Database error",
                "detail": detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
