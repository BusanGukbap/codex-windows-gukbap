#!/usr/bin/env python3
"""Mechanical checks for an LLM wiki.

Usage: lint.py [PATH]   PATH defaults to the current directory; any path inside the wiki works.
Exit status: 0 = clean, 1 = findings printed, 2 = no wiki root found, 3 = lint itself failed.
Never modifies files.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import unquote

CORE_TYPES = {"sources": "source", "entities": "entity", "concepts": "concept"}
REQUIRED_FIELDS = ("title", "type", "sources", "updated")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SHA_RE = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code}: {self.message}"


class FrontmatterError(ValueError):
    def __init__(self, line: int, message: str) -> None:
        super().__init__(message)
        self.line = line


def find_root(start: Path) -> Path | None:
    """Walk up from start to the first directory that looks like a wiki root."""
    start = start.resolve()
    for d in (start, *start.parents):
        if (
            (d / "CLAUDE.md").is_file()
            and (d / "index.md").is_file()
            and (d / "raw").is_dir()
            and (d / "wiki").is_dir()
        ):
            return d
    return None


def parse_frontmatter(text: str) -> dict[str, str | list[str]] | None:
    """Parse the restricted frontmatter subset: flat `key: value` and inline `[a, b]` lists."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: dict[str, str | list[str]] = {}
    for number, raw in enumerate(lines[1:], start=2):
        line = raw.strip()
        if line == "---":
            return data
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        key = key.strip()
        if not sep or not key or " " in key:
            raise FrontmatterError(number, f"not a 'key: value' line: {raw.strip()}")
        value = value.strip()
        if value.startswith("["):
            if not value.endswith("]"):
                raise FrontmatterError(number, f"unterminated list for '{key}'")
            inner = value[1:-1].strip()
            data[key] = [item.strip() for item in inner.split(",") if item.strip()] if inner else []
        else:
            data[key] = value
    raise FrontmatterError(1, "frontmatter block is not closed with '---'")


def iter_links(text: str) -> list[tuple[int, str]]:
    """Relative link targets outside code, as (line number, target without #anchor)."""
    links = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RE.finditer(INLINE_CODE_RE.sub("", line)):
            target = match.group(1)
            if "://" in target or target.startswith(("mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            if target:
                links.append((number, target))
    return links


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def wiki_pages(root: Path) -> list[Path]:
    return sorted((root / "wiki").rglob("*.md"))


def resolve_links(path: Path, text: str) -> list[tuple[int, str, Path]]:
    """(line, target as written, resolved absolute path) for each relative link in a file."""
    return [(number, target, (path.parent / target).resolve()) for number, target in iter_links(text)]


def check_links(root: Path, pages: dict[Path, str]) -> list[Finding]:
    findings = []
    index = root / "index.md"
    for path, text in [(index, index.read_text(encoding="utf-8")), *pages.items()]:
        code = "index-dangling" if path == index else "broken-link"
        for number, target, resolved in resolve_links(path, text):
            if not resolved.exists():
                findings.append(Finding(rel(root, path), number, code, f"link target does not exist: {target}"))
    return findings


def check_index(root: Path, pages: dict[Path, str]) -> list[Finding]:
    index = root / "index.md"
    listed = {resolved for _, _, resolved in resolve_links(index, index.read_text(encoding="utf-8"))}
    return [
        Finding(rel(root, page), 1, "index-missing", "page is not linked from index.md")
        for page in pages
        if page not in listed
    ]


def check_orphans(root: Path, pages: dict[Path, str]) -> list[Finding]:
    inbound: set[Path] = set()
    for page, text in pages.items():
        inbound |= {resolved for _, _, resolved in resolve_links(page, text) if resolved != page}
    return [
        Finding(rel(root, page), 1, "orphan", "no other wiki page links here (index.md does not count)")
        for page in pages
        if page not in inbound
    ]


def source_problems(root: Path, page: Path, text: str, fm: dict[str, str | list[str]]) -> list[tuple[int, str]]:
    problems = [(1, f"missing field: {field}") for field in ("raw", "origin") if not fm.get(field)]
    raw = fm.get("raw")
    if isinstance(raw, str) and raw:
        if not raw.startswith("raw/") or not (root / raw).is_file():
            problems.append((1, f"raw is not an existing file under raw/: {raw}"))
        elif (root / raw).resolve() not in {r for _, _, r in resolve_links(page, text)}:
            problems.append((1, f"source page does not link to its raw file: {raw}"))
        commit = fm.get("commit")
        if raw.startswith("raw/code/") and not (isinstance(commit, str) and SHA_RE.fullmatch(commit)):
            problems.append((1, "code source needs commit: <40-char SHA>"))
    return problems


def frontmatter_problems(root: Path, page: Path, text: str) -> list[tuple[int, str]]:
    try:
        fm = parse_frontmatter(text)
    except FrontmatterError as error:
        return [(error.line, str(error))]
    if fm is None:
        return [(1, "missing frontmatter block")]
    missing = [(1, f"missing field: {field}") for field in REQUIRED_FIELDS if fm.get(field, "") == ""]
    if missing:
        return missing

    parts = page.relative_to(root / "wiki").parts
    if len(parts) < 2:
        return [(1, "page must live in a type folder under wiki/")]
    problems = []
    folder, page_type = parts[0], fm["type"]
    expected = CORE_TYPES.get(folder)
    if expected and page_type != expected:
        problems.append((1, f"type '{page_type}' does not match folder '{folder}' (expected '{expected}')"))

    sources = fm["sources"]
    if not isinstance(sources, list):
        problems.append((1, "sources must be an inline list like [a, b]"))
    else:
        if page_type != "source" and not sources:
            problems.append((1, "sources must list at least one source page"))
        problems += [(1, f"sources entry does not exist: {s}") for s in sources if not (root / s).is_file()]

    updated = fm["updated"]
    if not (isinstance(updated, str) and DATE_RE.fullmatch(updated) and _is_date(updated)):
        problems.append((1, f"updated is not a YYYY-MM-DD date: {updated}"))

    if page_type == "source":
        problems += source_problems(root, page, text, fm)
    return problems


def _is_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def check_frontmatter(root: Path, pages: dict[Path, str]) -> list[Finding]:
    return [
        Finding(rel(root, page), line, "frontmatter", message)
        for page, text in pages.items()
        for line, message in frontmatter_problems(root, page, text)
    ]


def check_raw_modified(root: Path, pages: dict[Path, str]) -> list[Finding]:
    """Tracked files under raw/ modified, deleted, or retyped since HEAD. Silent outside git."""
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "-C", str(root), "diff", "--name-only",
             "--relative", "--no-renames", "--diff-filter=MDT", "HEAD", "--", "raw"],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    return [
        Finding(path, 1, "raw-modified", "tracked raw file differs from HEAD; raw/ is append-only")
        for path in result.stdout.splitlines()
        if path
    ]


CHECKS = [check_links, check_index, check_orphans, check_frontmatter, check_raw_modified]


def lint(root: Path) -> list[Finding]:
    pages: dict[Path, str] = {}
    findings = []
    for path in wiki_pages(root):
        try:
            pages[path] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(rel(root, path), 1, "frontmatter", "file is not valid UTF-8"))
    findings += (finding for check in CHECKS for finding in check(root, pages))
    return sorted(findings)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = find_root(Path(args[0]) if args else Path.cwd())
    if root is None:
        print("lint.py: no wiki root found (need CLAUDE.md, index.md, raw/, wiki/)", file=sys.stderr)
        return 2
    try:
        findings = lint(root)
    except Exception as error:
        print(f"lint.py: error: {error}", file=sys.stderr)
        return 3
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
