"""Induce a stopped frame stream to verify timeout and child process cleanup."""

import ctypes
import os
from pathlib import Path
import sys

from process_watchdog import run_logged


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    scratch = project / "build/watchdog-test"
    scratch.mkdir(parents=True, exist_ok=True)
    log = scratch / "stall.log"
    fixture = (
        "import subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
        "print('PROGRESS frame=1 child=%d' % child.pid, flush=True); time.sleep(30)"
    )
    try:
        run_logged([sys.executable, "-c", fixture], project, log,
                   "PROGRESS ", timeout=5, stall_timeout=0.5)
    except TimeoutError as error:
        assert "no completed frame" in str(error)
        assert "PROGRESS frame=1" in str(error)
    else:
        raise AssertionError("Stalled fixture did not time out")
    text = log.read_text()
    child_pid = int(text.split("child=", 1)[1].split()[0])
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, child_pid)
        if handle:
            status = ctypes.c_ulong()
            assert kernel.GetExitCodeProcess(handle, ctypes.byref(status))
            kernel.CloseHandle(handle)
            assert status.value != 259, "Watchdog left a child process running"
    print("PASS watchdog: stalled frame logged; spawned process tree stopped")


if __name__ == "__main__":
    main()
