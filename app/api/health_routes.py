from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.observability import get_metrics_snapshot
from app.core.observability import get_metrics_prometheus
from app.db.session import db_ready

router = APIRouter(prefix="/health")


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness() -> dict[str, str]:
    if not db_ready():
        raise HTTPException(status_code=503, detail="database is not ready")
    return {"status": "ready"}


@router.get("/metrics")
def metrics() -> dict[str, dict[str, float | int]]:
    return get_metrics_snapshot()


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
def metrics_prometheus() -> str:
    return get_metrics_prometheus()
