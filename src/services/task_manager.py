import asyncio
import os
import signal
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import AsyncGenerator, Optional, Any
from pathlib import Path

# ── Dual-Layer Logging Configuration ────────────────────────────────────────

# 1. System Logger (Standard app logs)
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
    - Raw output → Rotating persistent log (/tmp/music-curator.log)
    - Status/Result updates → n8n (filtered)
    """
    async def run_task(self, command: str, endpoint: str, request: Optional[Any] = None) -> AsyncGenerator[str, None]:
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
            start_msg = f"Task started: {endpoint} (PID: {process.pid}, PGID: {pgid})"
            task_logger.info(start_msg)
            yield f"{start_msg}\n"
            
            while True:
                try:
                    line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                    if not line:
                        break
                    
                    decoded_line = line.decode().strip()
                    if decoded_line:
                        # 1. ALWAYS route to persistent task log
                        task_logger.info(f"[{endpoint}] {decoded_line}")
                        
                        # 2. ONLY yield high-level status or results to n8n
                        lower_line = decoded_line.lower()
                        if any(x in lower_line for x in ["status:", "result:", "error:", "processed:"]):
                            yield f"{decoded_line}\n"
                        
                except asyncio.TimeoutError:
                    if request and await request.is_disconnected():
                        logger.warning(f"Proactive disconnect detected for {endpoint}")
                        raise asyncio.CancelledError()
                    continue
            
            return_code = await process.wait()
            finish_msg = f"Task {endpoint} finished with code {return_code}"
            task_logger.info(finish_msg)
            yield f"{finish_msg}\n"

        except asyncio.CancelledError:
            if pgid:
                cancel_msg = f"Cancelling task {endpoint} (PGID: {pgid})..."
                task_logger.warning(cancel_msg)
                if process and process.returncode is None:
                    try:
                        os.killpg(pgid, signal.SIGTERM)
                        await asyncio.sleep(0.5)
                        if process.returncode is None:
                            os.killpg(pgid, signal.SIGKILL)
                            task_logger.info(f"Task {endpoint} forcefully killed.")
                    except ProcessLookupError:
                        pass
            raise
            
        except Exception as e:
            err_msg = f"Internal Error in TaskManager for {endpoint}: {str(e)}"
            task_logger.error(err_msg)
            yield f"ERROR: {err_msg}\n"

# Global instance
task_manager = TaskManager()
