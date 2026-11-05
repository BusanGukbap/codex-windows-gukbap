#!/usr/bin/env python3
"""Preview or install this personal skill bundle without replacing user settings."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys
import uuid


BEGIN = "<!-- BEGIN CLAUDE-CODE-STEAL PERSONAL GUIDANCE -->"
END = "<!-- END CLAUDE-CODE-STEAL PERSONAL GUIDANCE -->"
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache"}


class InstallError(Exception):
    pass


@dataclass(frozen=True)
class Write:
    path: Path
    data: bytes
    before: bytes | None
    replace_required: bool


def absolute(value: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(value)))


def plain_path(path: Path) -> None:
    """Reject symlinks and Windows junctions before reading or writing through them."""
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise InstallError(f"Refusing a symlink or reparse point: {part}")


def existing(path: Path) -> bytes | None:
    plain_path(path)
    if not path.exists():
        return None
    if not path.is_file():
        raise InstallError(f"Expected a regular file: {path}")
    return path.read_bytes()


def source_files(root: Path):
    plain_path(root)
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
        for name in dirs:
            plain_path(Path(directory) / name)
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            path = Path(directory) / name
            plain_path(path)
            yield path


def guidance_data(before: bytes | None, fragment: bytes) -> tuple[bytes, bool]:
    try:
        old = (before or b"").decode("utf-8-sig").replace("\r\n", "\n")
        body = fragment.decode("utf-8-sig").replace("\r\n", "\n").strip()
    except UnicodeDecodeError as error:
        raise InstallError("Guidance files must use UTF-8.") from error
    if BEGIN in body or END in body:
        raise InstallError("The guidance fragment must not contain installer markers.")
    if old.count(BEGIN) != old.count(END) or old.count(BEGIN) > 1:
        raise InstallError("Existing guidance has incomplete or duplicate managed markers.")
    block = f"{BEGIN}\n{body}\n{END}"
    managed = BEGIN in old
    if managed:
        start, stop = old.index(BEGIN), old.index(END)
        if stop < start:
            raise InstallError("Existing guidance markers are out of order.")
        result = old[:start] + block + old[stop + len(END):]
    else:
        separator = "" if not old or old.endswith("\n\n") else "\n" if old.endswith("\n") else "\n\n"
        result = old + separator + block + "\n"
    newline = "\r\n" if before and b"\r\n" in before else "\n"
    bom = b"\xef\xbb\xbf" if before and before.startswith(b"\xef\xbb\xbf") else b""
    return bom + result.replace("\n", newline).encode("utf-8"), managed


def plan_install(source: Path, home: Path, codex_home: Path, with_guidance: bool = False, with_personal_skills: bool = False) -> tuple[list[Write], int]:
    source, home, codex_home = map(absolute, (source, home, codex_home))
    for root in (source, home, codex_home):
        plain_path(root)
    skill_source = source / "skills"
    if not skill_source.is_dir():
        raise InstallError(f"Skill source directory is missing: {skill_source}")
    sources = [skill_source]
    if with_personal_skills:
        personal_source = source / "personal-skills"
        plain_path(personal_source)
        if not personal_source.is_dir():
            raise InstallError(f"Personal skill source directory is missing: {personal_source}")
        sources.append(personal_source)
    skills = sorted((path for directory in sources for path in directory.iterdir() if path.is_dir()), key=lambda path: path.name)
    if not skills:
        raise InstallError("The bundle has no skills to install.")
    names = [skill.name.casefold() for skill in skills]
    if len(names) != len(set(names)):
        raise InstallError("Duplicate source skill names in the core and personal bundles.")
    roots = list(dict.fromkeys((home / ".agents" / "skills", home / ".codex" / "skills", codex_home / "skills")))
    writes: list[Write] = []
    unchanged = 0
    for skill in skills:
        plain_path(skill)
        if not (skill / "SKILL.md").is_file():
            raise InstallError(f"Skill has no SKILL.md: {skill}")
        candidates = [root / skill.name for root in roots]
        for target in candidates:
            plain_path(target)
        present = [target for target in candidates if target.exists()]
        if len(present) > 1:
            raise InstallError(f"Duplicate skill '{skill.name}'; keep one installation before retrying: " + ", ".join(map(str, present)))
        destination = present[0] if present else home / ".agents" / "skills" / skill.name
        for file in source_files(skill):
            target = destination / file.relative_to(skill)
            data, before = file.read_bytes(), existing(target)
            if data == before:
                unchanged += 1
            else:
                writes.append(Write(target, data, before, before is not None))
    if with_guidance:
        target = codex_home / "AGENTS.md"
        before = existing(target)
        fragment = existing(source / "codex" / "AGENTS.md")
        if fragment is None:
            raise InstallError("The optional codex/AGENTS.md guidance fragment is missing.")
        data, managed = guidance_data(before, fragment)
        if data == before:
            unchanged += 1
        else:
            writes.append(Write(target, data, before, managed))
    return writes, unchanged


def atomic_write(path: Path, data: bytes) -> None:
    plain_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.install-{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def apply(writes: list[Write], codex_home: Path, replace: bool = False) -> Path | None:
    conflicts = [item.path for item in writes if item.replace_required and not replace]
    if conflicts:
        raise InstallError("Existing files differ; review the preview and use --replace: " + ", ".join(map(str, conflicts)))
    # Validate the whole plan before creating directories or backing up files.
    for item in writes:
        if existing(item.path) != item.before:
            raise InstallError(f"Destination changed after preview: {item.path}")
    originals = [item for item in writes if item.before is not None]
    backup = None
    if originals:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        backup = codex_home / "backups" / "claude-code-steal" / stamp
        plain_path(backup)
        manifest = []
        for index, item in enumerate(originals):
            saved = Path(f"{index:04d}") / item.path.name
            atomic_write(backup / saved, item.before)
            manifest.append({"destination": str(item.path), "backup": saved.as_posix()})
        atomic_write(backup / "manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    for item in writes:
        if existing(item.path) != item.before:
            raise InstallError(f"Destination changed while installing: {item.path}")
        atomic_write(item.path, item.data)
    return backup


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the previewed changes")
    parser.add_argument("--replace", action="store_true", help="allow differing managed files, saving originals first")
    parser.add_argument("--home", type=Path, help="use an isolated profile home; ignores inherited CODEX_HOME")
    parser.add_argument("--codex-home", type=Path, help="explicit Codex config directory (overrides CODEX_HOME)")
    parser.add_argument("--with-guidance", action="store_true", help="merge the optional personal guidance block into AGENTS.md")
    parser.add_argument("--with-personal-skills", action="store_true", help="also include the optional frequently used skill snapshots")
    args = parser.parse_args(argv)
    home = absolute(args.home if args.home is not None else Path.home())
    selected = args.codex_home or (None if args.home is not None else os.environ.get("CODEX_HOME")) or home / ".codex"
    codex_home = absolute(selected)
    try:
        writes, unchanged = plan_install(Path(__file__).resolve().parents[1], home, codex_home, args.with_guidance, args.with_personal_skills)
        mode = "APPLY" if args.apply else "PREVIEW (no files written)"
        print(mode)
        print(f"Profile: {home}\nCodex config: {codex_home}")
        for item in writes:
            action = "REPLACE" if item.replace_required else "UPDATE" if item.before is not None else "CREATE"
            print(f"{action} {item.path}")
        print(f"Changed files: {len(writes)}; unchanged files: {unchanged}")
        if args.apply:
            backup = apply(writes, codex_home, args.replace)
            if backup:
                print(f"Originals saved to: {backup}")
            print("Installation complete. Restart Codex to refresh its skill catalog.")
        elif any(item.replace_required for item in writes):
            print("Existing files differ. --apply requires --replace for these replacements.")
        return 0
    except (InstallError, OSError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
