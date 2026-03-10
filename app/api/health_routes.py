from fastapi import APIRouter, HTTPException

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
