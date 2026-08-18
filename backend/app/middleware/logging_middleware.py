import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(f"Incoming Request: {request.method} {request.url.path} from IP: {client_ip}")
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(
                f"Completed Request: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Completed in {process_time:.2f}ms"
            )
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Failed Request: {request.method} {request.url.path} - "
                f"Unhandled Exception: {str(exc)} after {process_time:.2f}ms"
            )
            raise
