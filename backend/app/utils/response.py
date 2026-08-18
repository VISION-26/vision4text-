from typing import Any, Dict, Optional, Generic, TypeVar
from pydantic import BaseModel
from fastapi.responses import JSONResponse

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[Any] = None


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = 200
) -> JSONResponse:
    """
    Standardized success JSON response formatter.
    """
    content = {
        "success": True,
        "message": message,
        "data": data
    }
    return JSONResponse(status_code=status_code, content=content)


def error_response(
    message: str = "Operation failed",
    errors: Any = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Standardized error JSON response formatter.
    """
    content = {
        "success": False,
        "message": message,
        "errors": errors
    }
    return JSONResponse(status_code=status_code, content=content)
