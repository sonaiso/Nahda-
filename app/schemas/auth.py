from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=128)
    role: str = Field(default="service")
    bootstrap_key: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
