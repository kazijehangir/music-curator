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
    mock_proc.stdout = AsyncMock()
    mock_proc.stdout.__aiter__.return_value = [b"line1\n", b"line2\n"]
    mock_proc.wait.return_value = 0
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
    mock_proc.stdout = AsyncMock()
    mock_proc.returncode = None
    
    # Simulate an infinite stream that gets cancelled
    async def infinite_stream():
        yield b"working...\n"
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass
        yield b"done\n"
        
    mock_proc.stdout.__aiter__.side_effect = infinite_stream
    
    manager = TaskManager()
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
         patch("os.killpg") as mock_killpg, \
         patch("os.getpgid", return_value=1010), \
         patch("asyncio.sleep", return_value=None): # Speed up fallback
         
        gen = manager.run_task("analyze", "/api/analyze")
        await gen.__anext__() # Start and get first line
        
        # Simulate cancellation
        with pytest.raises(asyncio.CancelledError):
            await gen.athrow(asyncio.CancelledError)
            
        # Verify SIGTERM then SIGKILL
        mock_killpg.assert_any_call(1010, signal.SIGTERM)
        mock_killpg.assert_any_call(1010, signal.SIGKILL)
