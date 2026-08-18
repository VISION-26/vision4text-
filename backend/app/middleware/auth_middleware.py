from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for intercepting and preprocessing request auth tokens or session headers if needed.
    """
    async def dispatch(self, request: Request, call_next):
        # Attach token tracking or authorization context if header exists
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            request.state.raw_token = token
        else:
            request.state.raw_token = None

        return await call_next(request)
