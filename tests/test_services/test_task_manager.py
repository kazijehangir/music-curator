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
    
    # Mock readline to return two lines then EOF (empty bytes)
    mock_proc.stdout.readline.side_effect = [
        b"line1\n",
        b"line2\n",
        b""
    ]
    mock_proc.wait = AsyncMock(return_value=0)
    mock_proc.returncode = 0
    
    manager = TaskManager()
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
         patch("os.getpgid", return_value=999):
        lines = []
        async for line in manager.run_task("discover", "/api/discover"):
            lines.append(line)
            
    assert "Task started for /api/discover (PID: 999)\n" in lines
    assert "line1\n" in lines
    assert "line2\n" in lines
    assert "Task completed successfully.\n" in lines

@pytest.mark.asyncio
async def test_task_manager_cancellation():
    mock_proc = AsyncMock()
    mock_proc.pid = 1010
    mock_proc.returncode = None
    
    # Simulate a silent process that would time out the readline()
    async def silent_readline():
        await asyncio.sleep(10)
        return b""
        
    mock_proc.stdout.readline.side_effect = silent_readline
    
    # Mock request with disconnect detection
    mock_request = AsyncMock()
    # Ensure it returns True when called
    mock_request.is_disconnected = AsyncMock(return_value=True)
    
    manager = TaskManager()
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
         patch("os.killpg") as mock_killpg, \
         patch("os.getpgid", return_value=1010), \
         patch("asyncio.sleep", return_value=None):
         
        gen = manager.run_task("analyze", "/api/analyze", mock_request)
        
        # 1. First yield is the "Task started" message
        msg = await gen.__anext__()
        assert "Task started" in msg
        
        # 2. Next yield should trigger the heartbeat check and raise CancelledError
        # We wrap the wait_for call to force a timeout
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(asyncio.CancelledError):
                await gen.__anext__()
            
        # Verify escalation logic happened
        mock_killpg.assert_any_call(1010, signal.SIGTERM)
        mock_killpg.assert_any_call(1010, signal.SIGKILL)
