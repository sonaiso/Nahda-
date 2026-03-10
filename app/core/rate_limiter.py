from collections import deque
from threading import Lock
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._entries: dict[str, deque[float]] = {}
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        if request.url.path in {"/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = monotonic()
        window_start = now - settings.rate_limit_window_seconds

        with self._lock:
            bucket = self._entries.setdefault(client_ip, deque())
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= settings.rate_limit_requests_per_window:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(settings.rate_limit_window_seconds)},
                )

            bucket.append(now)

        return await call_next(request)
