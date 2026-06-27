import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app

@pytest.mark.asyncio
async def test_cors_disallowed_origin_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options("/", headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "GET"})
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_cors_allowed_origin_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options("/", headers={"Origin": "http://127.0.0.1:8090", "Access-Control-Request-Method": "GET"})
        assert response.status_code == 200
