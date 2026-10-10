"""Bound local test processes and retain their last completed progress record."""

import os
from pathlib import Path
import subprocess
import time


def run_logged(command: list[str], cwd: Path, log: Path,
               progress_prefix: str, timeout: float = 600,
               stall_timeout: float = 60) -> int:
    if timeout <= 0 or stall_timeout <= 0:
        raise ValueError("Timeouts must be positive")
    last_progress = "<no completed progress record>"
    started = last_advance = time.monotonic()
    offset = 0
    pending = ""
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=cwd, stdout=output,
                                   stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                with log.open("r", encoding="utf-8", errors="replace") as reader:
                    reader.seek(offset)
                    pending += reader.read()
                    offset = reader.tell()
                lines = pending.split("\n")
                pending = lines.pop()
                for line in lines:
                    if line.startswith(progress_prefix) and line != last_progress:
                        last_progress = line
                        last_advance = time.monotonic()
                now = time.monotonic()
                reason = None
                if now - started >= timeout:
                    reason = f"total test deadline ({timeout}s)"
                elif now - last_advance >= stall_timeout:
                    reason = f"no completed frame for {stall_timeout}s"
                if reason:
                    output.write(f"\nWATCHDOG: {reason}; last: {last_progress}\n")
                    output.flush()
                    raise TimeoutError(f"{reason}; {last_progress}; inspect {log}")
                time.sleep(min(0.25, stall_timeout / 4))
            return process.returncode
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    # Only the tree of the process spawned above, including its
                    # debugger inferior. Killing GDB alone can orphan the game.
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if process.poll() is None:
                    process.kill()
                process.wait()
