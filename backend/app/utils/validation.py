import os
from fastapi import UploadFile
from app.core.config import settings
from app.utils.exceptions import InvalidFileFormatException, FileTooLargeException


def validate_image_extension(filename: str) -> str:
    """
    Validate file extension against allowed PNG, JPG, JPEG formats.
    """
    if not filename or "." not in filename:
        raise InvalidFileFormatException("Uploaded file must have an image extension (.png, .jpg, .jpeg)")
        
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise InvalidFileFormatException(
            f"Invalid file extension '.{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    return ext


def validate_image_file(file: UploadFile) -> None:
    """
    Validate upload file extension and size limit.
    """
    validate_image_extension(file.filename)
    
    # Check size if available on content headers
    if file.size and file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeException(
            f"File size {file.size / (1024*1024):.2f}MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )
