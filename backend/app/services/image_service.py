import os
import tempfile
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


class ImageService:
    @staticmethod
    async def save_uploaded_image(file: UploadFile) -> tuple[str, int, str]:
        filename = file.filename or "upload"
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only PNG, JPG, and JPEG files are allowed.",
            )

        data = bytearray()
        while chunk := await file.read(1024 * 1024):
            data.extend(chunk)
            if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                )
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")

        try:
            with Image.open(BytesIO(data)) as image:
                image.verify()
            with Image.open(BytesIO(data)) as image:
                width, height = image.size
                pixel_count = width * height
                image_format = (image.format or "").upper()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Uploaded file is not a valid or safe image.",
            )

        if pixel_count > settings.MAX_IMAGE_PIXELS:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image dimensions are too large ({width}×{height}).",
            )
        if min(width, height) < settings.MIN_IMAGE_SIDE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Image is too small for reliable inspection. Minimum side is {settings.MIN_IMAGE_SIDE}px.",
            )
        expected_formats = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG"}
        if image_format and expected_formats.get(extension) != image_format:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Image extension does not match the actual image format.",
            )

        output_name = f"{uuid.uuid4().hex}.{extension}"
        upload_dir = Path(settings.abs_upload_dir)
        target = upload_dir / output_name
        # Atomic same-filesystem write: interrupted uploads never leave a partial
        # file that later appears to be a valid inspection source.
        fd, tmp_name = tempfile.mkstemp(prefix=".upload-", suffix=f".{extension}", dir=upload_dir)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_name, target)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

        return f"{settings.UPLOAD_DIR}/{output_name}", len(data), file.content_type or "image/jpeg"
