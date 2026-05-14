import sys
from fastapi.testclient import TestClient

try:
    from src.api.main import app
    from src.core.config import settings

    client = TestClient(app)

    # Make a dummy request to check if CORS headers are being applied correctly
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    print("Status:", response.status_code)
    print("Headers:", response.headers)

    assert response.status_code in [200, 204], "CORS request failed"
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000" or response.headers.get("access-control-allow-origin") == "*", "CORS allow origin not match"
    print("Test passed successfully.")
except Exception as e:
    print(f"Test failed with error: {e}")
