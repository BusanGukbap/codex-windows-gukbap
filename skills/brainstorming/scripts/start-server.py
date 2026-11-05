#!/usr/bin/env python3
"""Start the visual companion without Bash, WSL, or shell interpolation."""

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--url-host")
    parser.add_argument("--idle-timeout-minutes", type=int, default=240)
    parser.add_argument("--open", action="store_true", help="open only after user approval")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--foreground", "--no-daemon", action="store_true")
    mode.add_argument("--background", "--daemon", action="store_true")
    args = parser.parse_args()
    if args.idle_timeout_minutes < 1:
        parser.error("--idle-timeout-minutes must be positive")
    node = shutil.which("node")
    if not node:
        parser.error("Node.js is required for the visual companion")

    instance = secrets.token_urlsafe(32)
    if args.project_dir:
        base = args.project_dir.resolve() / ".superpowers" / "brainstorm"
        session = base / f"{int(time.time())}-{instance[:12]}"
        session.mkdir(parents=True, mode=0o700)
    else:
        session = Path(tempfile.mkdtemp(prefix="brainstorm-"))
        base = None
    state = session / "state"
    state.mkdir(mode=0o700)
    (session / "content").mkdir(mode=0o700)
    (state / "server-instance-id").write_text(instance + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "BRAINSTORM_DIR": str(session),
        "BRAINSTORM_HOST": args.host,
        "BRAINSTORM_URL_HOST": args.url_host or ("localhost" if args.host in ("127.0.0.1", "localhost") else args.host),
        "BRAINSTORM_IDLE_TIMEOUT_MS": str(args.idle_timeout_minutes * 60000),
        "BRAINSTORM_OWNER_PID": str(os.getpid()) if args.foreground else "",
    })
    if base:
        env["BRAINSTORM_PORT_FILE"] = str(base / ".last-port")
        env["BRAINSTORM_TOKEN_FILE"] = str(base / ".last-token")
    # A caller's environment must not open a browser without this explicit option.
    env.pop("BRAINSTORM_OPEN", None)
    if args.open:
        env["BRAINSTORM_OPEN"] = "1"
    command = [node, str(Path(__file__).with_name("server.cjs")), f"--brainstorm-server-id={instance}"]
    creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    log = None if args.foreground else (state / "server.log").open("wb")
    try:
        process = subprocess.Popen(
            command, env=env, stdin=subprocess.DEVNULL, stdout=log,
            stderr=log, creationflags=creationflags,
            start_new_session=os.name != "nt",
        )
    finally:
        if log:
            log.close()
    (state / "server.pid").write_text(str(process.pid) + "\n", encoding="ascii")
    if args.foreground:
        try:
            return process.wait()
        except KeyboardInterrupt:
            process.terminate()
            return process.wait()
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(json.dumps({"error": "server exited during startup", "state_dir": str(state)}))
            return 1
        info_file = state / "server-info"
        if info_file.is_file():
            try:
                info = json.loads(info_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                time.sleep(0.05)
                continue
            if info.get("type") == "server-started":
                print(json.dumps(info))
                return 0
        time.sleep(0.05)
    process.terminate()
    process.wait(timeout=5)
    print(json.dumps({"error": "server failed to start within eight seconds", "state_dir": str(state)}))
    return 1


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
