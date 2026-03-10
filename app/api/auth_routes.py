from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.auth import TokenRequest, TokenResponse
from app.security.auth import create_access_token

router = APIRouter(prefix="/auth")

_ALLOWED_ROLES = {"admin", "service", "read"}


@router.post("/token", response_model=TokenResponse)
def issue_token(payload: TokenRequest) -> TokenResponse:
    if payload.bootstrap_key != settings.auth_bootstrap_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bootstrap key")

    if payload.role not in _ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    token = create_access_token(subject=payload.subject, role=payload.role)
    return TokenResponse(
        access_token=token,
        expires_in_seconds=settings.auth_access_token_exp_minutes * 60,
    )
