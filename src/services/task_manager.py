import asyncio
import sys
import os
import signal
import logging
from typing import AsyncGenerator
from pathlib import Path

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Manages transient background tasks. 
    Runs CLI commands as subprocesses and yields logs in real-time.
    No persistent state is stored in the database.
    """
    async def run_task(self, command: str, endpoint: str) -> AsyncGenerator[str, None]:
        """
        Runs a CLI command as a subprocess and yields its output lines.
        """
        process = None
        
        try:
            # Start subprocess in a new process group for clean termination
            # Using start_new_session=True is the modern, safer way to os.setsid
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "src.cli", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True
            )
            
            pgid = os.getpgid(process.pid)
            logger.info(f"Task started for {endpoint} (PID: {process.pid}, PGID: {pgid})")
            yield f"Task started for {endpoint} (PID: {process.pid})\n"
            
            # Stream output
            async for line in process.stdout:
                decoded_line = line.decode().strip()
                if decoded_line:
                    yield f"{decoded_line}\n"
            
            # Wait for completion
            return_code = await process.wait()
            
            if return_code == 0:
                yield "Task completed successfully.\n"
            else:
                yield f"Task failed with exit code {return_code}.\n"

        except asyncio.CancelledError:
            # Triggered by client disconnect (StreamingResponse cancelled)
            logger.warning(f"Client disconnected for {endpoint}. Killing process group {pgid}...")
            
            if process and process.returncode is None:
                try:
                    # 1. Try SIGTERM first
                    os.killpg(pgid, signal.SIGTERM)
                    
                    # 2. Give it a short moment to exit gracefully, then SIGKILL
                    await asyncio.sleep(0.5)
                    if process.returncode is None:
                        os.killpg(pgid, signal.SIGKILL)
                        logger.info(f"Process group {pgid} killed with SIGKILL")
                except ProcessLookupError:
                    pass
            raise
            
        except Exception as e:
            logger.error(f"Error in TaskManager for {endpoint}: {e}")
            yield f"Internal Error: {str(e)}\n"

# Global instance
task_manager = TaskManager()
