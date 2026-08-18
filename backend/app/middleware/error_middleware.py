import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import logger


class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"Global Unhandled Exception captured: {exc}")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "An internal server error occurred.",
                    "detail": "Internal Server Error"
                }
            )
