import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from src.api.main import app

@pytest.mark.asyncio
async def test_cors_allowed_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # Preflight request from allowed origin
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Example"
        }
        response = await client.options("/api/discover", headers=headers)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_cors_disallowed_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # Preflight request from disallowed origin
        headers = {
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Example"
        }
        response = await client.options("/api/discover", headers=headers)
        assert response.status_code == 400
        assert response.text == "Disallowed CORS origin"
