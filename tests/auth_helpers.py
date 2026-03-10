from fastapi.testclient import TestClient

from app.core.config import settings


def get_auth_headers(client: TestClient, role: str = "service") -> dict[str, str]:
    response = client.post(
        "/auth/token",
        json={
            "subject": "test-user",
            "role": role,
            "bootstrap_key": settings.auth_bootstrap_key,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
