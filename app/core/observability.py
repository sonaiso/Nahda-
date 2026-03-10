import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.tracing import extract_context_from_headers
from app.core.tracing import get_tracer

logger = logging.getLogger("nahda.access")


@dataclass
class MetricBucket:
    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0


class MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._buckets: dict[str, MetricBucket] = defaultdict(MetricBucket)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    def record(self, route_key: str, status_code: int, latency_ms: float) -> None:
        with self._lock:
            bucket = self._buckets[route_key]
            bucket.total_requests += 1
            bucket.total_latency_ms += latency_ms
            if status_code >= 400:
                bucket.total_errors += 1

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        with self._lock:
            data: dict[str, dict[str, float | int]] = {}
            for key, bucket in self._buckets.items():
                avg_latency = (
                    bucket.total_latency_ms / bucket.total_requests if bucket.total_requests else 0.0
                )
                data[key] = {
                    "requests": bucket.total_requests,
                    "errors": bucket.total_errors,
                    "avg_latency_ms": round(avg_latency, 3),
                }
            return data


METRICS = MetricsStore()


def reset_metrics() -> None:
    METRICS.reset()


def get_metrics_snapshot() -> dict[str, dict[str, float | int]]:
    return METRICS.snapshot()


def get_metrics_prometheus() -> str:
    snapshot = METRICS.snapshot()
    lines = [
        "# HELP nahda_requests_total Total HTTP requests per route.",
        "# TYPE nahda_requests_total counter",
        "# HELP nahda_errors_total Total HTTP errors per route.",
        "# TYPE nahda_errors_total counter",
        "# HELP nahda_latency_avg_ms Average latency in milliseconds per route.",
        "# TYPE nahda_latency_avg_ms gauge",
    ]

    for route, values in snapshot.items():
        route_label = route.replace('"', "\\\"")
        lines.append(f'nahda_requests_total{{route="{route_label}"}} {values["requests"]}')
        lines.append(f'nahda_errors_total{{route="{route_label}"}} {values["errors"]}')
        lines.append(f'nahda_latency_avg_ms{{route="{route_label}"}} {values["avg_latency_ms"]}')

    return "\n".join(lines) + "\n"


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.observability_enabled:
            return await call_next(request)

        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()

        tracer = get_tracer()
        context = extract_context_from_headers(dict(request.headers.items()))
        trace_id = ""
        with tracer.start_as_current_span(
            "http.request",
            context=context,
            attributes={
                "http.method": request.method,
                "http.route": request.url.path,
                "http.request_id": request_id,
            },
        ) as span:
            response = await call_next(request)

            latency_ms = (time.perf_counter() - started) * 1000
            path = request.url.path if settings.observability_include_path_labels else "all"
            route_key = f"{request.method} {path}"

            METRICS.record(route_key=route_key, status_code=response.status_code, latency_ms=latency_ms)
            response.headers["X-Request-ID"] = request_id
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.latency_ms", round(latency_ms, 3))

            span_context = span.get_span_context()
            if span_context.is_valid:
                trace_id = format(span_context.trace_id, "032x")
                response.headers["X-Trace-ID"] = trace_id

        logger.info(
            json.dumps(
                {
                    "event": "http_access",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency_ms, 3),
                    "trace_id": trace_id,
                }
            )
        )

        return response
