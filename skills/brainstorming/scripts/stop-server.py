#!/usr/bin/env python3
"""Stop only a companion process matching this session's random instance ID.

Session content is retained on every platform; no directory is recursively deleted.
"""

import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def command_line(pid):
    if os.name == "nt":
        script = (
            "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
            f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    proc_file = Path(f"/proc/{pid}/cmdline")
    if proc_file.is_file():
        return proc_file.read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
    result = subprocess.run(["ps", "-ww", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def process_alive(pid):
    if os.name == "nt":
        # os.kill(pid, 0) is not a safe liveness probe on Windows.
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:  # ERROR_INVALID_PARAMETER: this PID no longer exists.
                return False
            raise PermissionError(f"cannot query process {pid} (Windows error {error})")
        try:
            code = ctypes.c_uint32()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def mark_stopped(state, reason):
    for name in ("server.pid", "server-instance-id", "server-info"):
        (state / name).unlink(missing_ok=True)
    (state / "server-stopped").write_text(
        json.dumps({"reason": reason, "timestamp": int(time.time() * 1000)}) + "\n", encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dir", type=Path)
    args = parser.parse_args()
    state = args.session_dir.resolve() / "state"
    pid_file = state / "server.pid"
    if not pid_file.is_file():
        print(json.dumps({"status": "not_running"}))
        return 0
    try:
        pid = int(pid_file.read_text(encoding="ascii").strip())
        instance = (state / "server-instance-id").read_text(encoding="ascii").strip()
    except (OSError, ValueError):
        print(json.dumps({"status": "invalid_metadata"}))
        return 1
    if pid < 1 or not re.fullmatch(r"[A-Za-z0-9_-]{32,64}", instance):
        print(json.dumps({"status": "invalid_metadata"}))
        return 1
    expected = re.compile(r'(?:^|[\s"])' + re.escape("--brainstorm-server-id=" + instance) + r'(?=$|[\s"])')
    try:
        alive = process_alive(pid)
    except OSError:
        print(json.dumps({"status": "failed", "error": "cannot query process; metadata retained"}))
        return 1
    try:
        actual_command = command_line(pid) if alive else ""
    except (OSError, subprocess.TimeoutExpired):
        actual_command = ""
    if alive and not actual_command:
        print(json.dumps({"status": "failed", "error": "cannot verify live process identity; metadata retained"}))
        return 1
    belongs_to_session = alive and bool(expected.search(actual_command))
    if not belongs_to_session:
        mark_stopped(state, "stale_pid")
        print(json.dumps({"status": "stale_pid"}))
        return 0
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 2
    while process_alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    if process_alive(pid):
        # Revalidate identity before a second signal, in case the PID was reused.
        if not expected.search(command_line(pid)):
            print(json.dumps({"status": "failed", "error": "process identity changed"}))
            return 1
        os.kill(pid, signal.SIGTERM if os.name == "nt" else signal.SIGKILL)
        time.sleep(0.1)
    if process_alive(pid):
        print(json.dumps({"status": "failed", "error": "process still running"}))
        return 1
    mark_stopped(state, "stop-server.py")
    print(json.dumps({"status": "stopped"}))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
