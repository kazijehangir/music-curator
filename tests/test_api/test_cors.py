import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app

@pytest.mark.asyncio
async def test_cors_allowed_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options(
            "/api/discover",
            headers={
                "Origin": "http://127.0.0.1:8090",
                "Access-Control-Request-Method": "POST"
            }
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8090"

@pytest.mark.asyncio
async def test_cors_disallowed_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options(
            "/api/discover",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST"
            }
        )
    assert response.status_code == 400
