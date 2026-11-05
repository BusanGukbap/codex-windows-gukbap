#!/usr/bin/env python3
"""Find the first test that creates an absent path; never remove that path.

Example: python find-polluter.py unwanted-file "src/**/*.test.ts"
Use --command pytest to choose a runner instead of the default npm test.
"""

import argparse
import glob
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pollution", type=Path)
    parser.add_argument("pattern")
    parser.add_argument("--command", nargs="+", default=["npm", "test"])
    args = parser.parse_args()
    if args.pollution.exists():
        parser.error("the pollution path already exists; choose an initially absent path")
    files = sorted(path for path in glob.glob(args.pattern, recursive=True) if Path(path).is_file())
    if not files:
        parser.error("no test files match the pattern")
    runner = shutil.which(args.command[0])
    if not runner:
        parser.error(f"test runner not found: {args.command[0]}")
    print(f"Found {len(files)} test files")
    for index, path in enumerate(files, 1):
        print(f"[{index}/{len(files)}] Testing: {path}", flush=True)
        # Avoid shell quoting of Unicode paths and Windows npm.cmd.
        command = [runner, *args.command[1:], path]
        if Path(runner).suffix.lower() in (".cmd", ".bat"):
            npm_entry = Path(runner).parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
            node = shutil.which("node")
            if Path(runner).stem.lower() != "npm" or not node or not npm_entry.is_file():
                parser.error("use a native executable or Python runner instead of a .cmd/.bat command")
            command = [node, str(npm_entry), *args.command[1:], path]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if args.pollution.exists():
            print(f"FOUND POLLUTER: {path}\nCreated: {args.pollution}")
            return 1
    print("No polluter found")
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
