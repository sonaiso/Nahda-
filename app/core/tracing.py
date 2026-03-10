from contextlib import contextmanager
import importlib
from typing import Any

from opentelemetry import propagate
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from app.core.config import settings

try:
    _otlp_module = importlib.import_module("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    OTLPExporterFactory: Any = getattr(_otlp_module, "OTLPSpanExporter", None)
except Exception:  # pragma: no cover
    OTLPExporterFactory = None

_TRACING_CONFIGURED = False


def setup_tracing() -> None:
    global _TRACING_CONFIGURED

    if _TRACING_CONFIGURED or not settings.otel_enabled:
        return

    resource = Resource(attributes={SERVICE_NAME: settings.otel_service_name})
    sampler = ParentBased(TraceIdRatioBased(settings.otel_sampling_ratio))
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter_name = settings.otel_exporter.lower().strip()
    exporter: SpanExporter | None = None

    if exporter_name == "console":
        exporter = ConsoleSpanExporter()
    elif exporter_name == "otlp" and OTLPExporterFactory is not None:
        exporter = OTLPExporterFactory(endpoint=settings.otel_otlp_endpoint)

    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True


def get_tracer():
    return trace.get_tracer(settings.otel_service_name)


def extract_context_from_headers(headers: dict[str, str]):
    return propagate.extract(headers)


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None):
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span
