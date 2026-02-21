import pytest
from unittest.mock import patch

def test_api_tag_endpoint(client, mock_pocketbase):
    # Mock task_manager.run_task to return an async generator
    async def mock_run_task(*args, **kwargs):
        yield "Task started\n"
        yield "STATUS: tagged 1 releases\n"
        yield "Task finished\n"

    with patch("src.api.endpoints.task_manager.run_task", side_effect=mock_run_task):
        response = client.post("/api/tag")
        
        assert response.status_code == 200
        # The response is now a text stream
        content = response.text
        assert "STATUS: tagged 1 releases" in content
