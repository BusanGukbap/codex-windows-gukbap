#!/usr/bin/env python3
"""Manually format changed C/C++ files from apply_patch or legacy hook JSON.

Only existing files resolving inside the supplied cwd are eligible. No hook is
registered automatically; pass a JSON event on stdin when explicitly enabled.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys


def changed_paths(payload):
    value = payload.get("tool_input", payload.get("input", {}))
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            pass
        else:
            if isinstance(decoded, (dict, str)):
                value = decoded
    if isinstance(value, dict):
        if value.get("file_path"):
            return [value["file_path"]]
        value = value.get("input", value.get("patch", value.get("command", "")))
    if not isinstance(value, str):
        return []
    prefixes = ("*** Add File: ", "*** Update File: ", "*** Move to: ")
    return [line[len(prefix):] for line in value.splitlines() for prefix in prefixes if line.startswith(prefix)]


def format_files(payload):
    names = changed_paths(payload)
    if not names:
        return 0
    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value:
        raise ValueError("cwd is required for file formatting")
    cwd = Path(cwd_value).resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError("cwd must be a directory")
    paths = []
    for name in names:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("file path must be a nonempty string")
        path = (cwd / name).resolve()
        if not path.is_relative_to(cwd):
            raise ValueError("refusing to format a file outside cwd")
        if path.is_file() and path.suffix.lower() in (".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hxx") and path not in paths:
            paths.append(path)
    if not paths or not any((root / ".clang-format").is_file() for root in (cwd, *cwd.parents)):
        return 0
    executable = shutil.which("clang-format")
    if not executable:
        raise RuntimeError("clang-format not found in PATH")
    for path in paths:
        subprocess.run([executable, "-i", str(path)], check=True, cwd=cwd)
    return len(paths)


def main():
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("event must be a JSON object")
        print(json.dumps({"formatted": format_files(payload)}))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
