from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class VisionTextException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class InvalidFileFormatException(VisionTextException):
    def __init__(self, detail: str = "Invalid file format. Allowed formats: PNG, JPG, JPEG"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FileTooLargeException(VisionTextException):
    def __init__(self, detail: str = "File size exceeds maximum allowed limit of 20MB"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ItemNotFoundException(VisionTextException):
    def __init__(self, item_name: str = "Resource", item_id: Any = None):
        detail = f"{item_name} with identifier '{item_id}' not found." if item_id else f"{item_name} not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedAccessException(VisionTextException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class PermissionDeniedException(VisionTextException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class PredictionServiceException(VisionTextException):
    def __init__(self, detail: str = "Error executing AI vision prediction model"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
