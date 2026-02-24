import pytest
import asyncio
import os
import signal
from unittest.mock import MagicMock, patch, AsyncMock, ANY
from src.services.task_manager import TaskManager

@pytest.mark.asyncio
async def test_task_manager_run_task_success():
    # Mock subprocess
    mock_proc = AsyncMock()
    mock_proc.pid = 999
    
    # Mock readline to return a mix of raw logs and status updates
    mock_proc.stdout.readline.side_effect = [
        b"raw debug log 1\n",
        b"STATUS: Analyzing 1/2\n",
        b"raw debug log 2\n",
        b"RESULT: Success\n",
        b""
    ]
    mock_proc.wait = AsyncMock(return_value=0)
    mock_proc.returncode = 0
    
    manager = TaskManager()
    
    # Mock the task_logger to verify raw routing
    with patch("src.services.task_manager.task_logger") as mock_task_logger, \
         patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
         patch("os.getpgid", return_value=999):
         
        lines = []
        async for line in manager.run_task("discover", "/api/discover"):
            lines.append(line)
            
    # Verify n8n output only has filtered lines
    assert any("Task started" in l for l in lines)
    assert "STATUS: Analyzing 1/2\n" in lines
    assert "RESULT: Success\n" in lines
    assert "raw debug log 1\n" not in lines # Should be filtered out
    
    # Verify raw logger received EVERYTHING
    mock_task_logger.info.assert_any_call("[/api/discover] raw debug log 1")
    mock_task_logger.info.assert_any_call("[/api/discover] STATUS: Analyzing 1/2")

@pytest.mark.asyncio
async def test_task_manager_cancellation():
    mock_proc = AsyncMock()
    mock_proc.pid = 1010
    mock_proc.returncode = None
    
    # Mock silent process
    async def silent_readline():
        await asyncio.sleep(10)
        return b""
    mock_proc.stdout.readline.side_effect = silent_readline
    
    mock_request = AsyncMock()
    mock_request.is_disconnected = AsyncMock(return_value=True)
    
    manager = TaskManager()
    
    with patch("src.services.task_manager.task_logger"), \
         patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
         patch("os.killpg") as mock_killpg, \
         patch("os.getpgid", return_value=1010), \
         patch("asyncio.sleep", return_value=None):
         
        gen = manager.run_task("analyze", "/api/analyze", mock_request)
        await gen.__anext__() # Consume start msg
        
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(asyncio.CancelledError):
                await gen.__anext__()
            
        mock_killpg.assert_any_call(1010, signal.SIGTERM)
        mock_killpg.assert_any_call(1010, signal.SIGKILL)

@pytest.mark.asyncio
async def test_task_manager_error_handling():
    manager = TaskManager()
    endpoint = "/api/test"

    # Mock create_subprocess_exec to raise an exception
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("Launch Failure")), \
         patch("src.services.task_manager.task_logger") as mock_task_logger:

        results = []
        async for line in manager.run_task("test", endpoint):
            results.append(line)

        assert len(results) == 1
        assert "ERROR: Internal Error in TaskManager for /api/test: Launch Failure" in results[0]
        mock_task_logger.error.assert_called_once_with("Internal Error in TaskManager for /api/test: Launch Failure")

@pytest.mark.asyncio
async def test_task_manager_readline_error_handling():
    mock_proc = AsyncMock()
    mock_proc.pid = 888
    mock_proc.stdout.readline.side_effect = Exception("Readline Error")

    manager = TaskManager()
    endpoint = "/api/test-readline"

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
         patch("os.getpgid", return_value=888), \
         patch("src.services.task_manager.task_logger") as mock_task_logger:

        results = []
        async for line in manager.run_task("test", endpoint):
            results.append(line)

        # Results should contain start msg and then the error
        assert any("Task started" in l for l in results)
        assert any("ERROR: Internal Error in TaskManager for /api/test-readline: Readline Error" in l for l in results)
        mock_task_logger.error.assert_called_once_with("Internal Error in TaskManager for /api/test-readline: Readline Error")
