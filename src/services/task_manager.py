import asyncio
import sys
import os
import signal
import logging
from logging.handlers import RotatingFileHandler
from typing import AsyncGenerator, Optional, Any
from pathlib import Path

# ── Dual-Layer Logging Configuration ────────────────────────────────────────

# 1. System Logger (Standard)
logger = logging.getLogger(__name__)

# 2. Task-Specific Persistent Log (Rotating)
# This captures EVERYTHING from subprocesses for local tail -f
TASK_LOG_FILE = "/tmp/music-curator.log"
task_log_handler = RotatingFileHandler(TASK_LOG_FILE, maxBytes=10*1024*1024, backupCount=3)
task_log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

task_logger = logging.getLogger("music_curator_tasks")
task_logger.setLevel(logging.INFO)
task_logger.addHandler(task_log_handler)
task_logger.propagate = False # Keep it out of standard app logs

class TaskManager:
    """
    Manages transient background tasks. 
    Runs CLI commands as subprocesses and yields logs in real-time.
    No persistent state is stored in the database.
    """
    async def run_task(self, command: str, endpoint: str, request: Optional[Any] = None) -> AsyncGenerator[str, None]:
        """
        Runs a CLI command and yields logs. 
        If 'request' is provided, proactively checks for client disconnect.
        """
        process = None
        pgid = None
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "src.cli", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True
            )
            
            pgid = os.getpgid(process.pid)
            logger.info(f"Task started for {endpoint} (PID: {process.pid}, PGID: {pgid})")
            yield f"Task started for {endpoint} (PID: {process.pid})\n"
            
            # Stream output with proactive disconnect check
            while True:
                try:
                    # Wait for output or 1s timeout
                    line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                    if not line:
                        break
                    
                    decoded_line = line.decode().strip()
                    if decoded_line:
                        yield f"{decoded_line}\n"
                        
                except asyncio.TimeoutError:
                    # If we haven't seen output for 1s, check if the client is still there
                    if request and await request.is_disconnected():
                        logger.warning(f"Proactive disconnect detected for {endpoint}")
                        raise asyncio.CancelledError()
                    continue
            
            # Wait for completion
            return_code = await process.wait()
            
            if return_code == 0:
                yield "Task completed successfully.\n"
            else:
                yield f"Task failed with exit code {return_code}.\n"

        except asyncio.CancelledError:
            # Triggered by client disconnect
            if pgid:
                logger.warning(f"Client disconnected for {endpoint}. Killing process group {pgid}...")
                if process and process.returncode is None:
                    try:
                        os.killpg(pgid, signal.SIGTERM)
                        await asyncio.sleep(0.5)
                        if process.returncode is None:
                            os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            raise
            
        except Exception as e:
            logger.error(f"Error in TaskManager for {endpoint}: {e}")
            yield f"Internal Error: {str(e)}\n"

# Global instance
task_manager = TaskManager()
