import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import lint


# --- helpers -----------------------------------------------------------------


def test_finding_formats_as_path_line_code_message():
    f = lint.Finding("wiki/concepts/a.md", 3, "broken-link", "link target does not exist: b.md")
    assert str(f) == "wiki/concepts/a.md:3: broken-link: link target does not exist: b.md"


def test_parse_frontmatter_returns_none_without_block():
    assert lint.parse_frontmatter("# Title\n\nbody\n") is None


def test_parse_frontmatter_reads_scalars_and_lists():
    text = (
        "---\n"
        "title: Blog: Transformer notes\n"
        "type: source\n"
        "sources: [a.md, b.md]\n"
        "empty: []\n"
        "origin: https://example.com/x#y\n"
        "updated: 2026-10-05\n"
        "---\n"
        "body\n"
    )
    assert lint.parse_frontmatter(text) == {
        "title": "Blog: Transformer notes",
        "type": "source",
        "sources": ["a.md", "b.md"],
        "empty": [],
        "origin": "https://example.com/x#y",
        "updated": "2026-10-05",
    }


def test_parse_frontmatter_keeps_hash_in_values():
    text = "---\ntitle: Issue #42\n---\n"
    assert lint.parse_frontmatter(text) == {"title": "Issue #42"}
    assert lint.parse_frontmatter("---\ntitle: #1 result\n---\n") == {"title": "#1 result"}


def test_parse_frontmatter_skips_comment_and_blank_lines():
    assert lint.parse_frontmatter("---\n# note\n\ntitle: X\n---\n") == {"title": "X"}


def test_parse_frontmatter_rejects_non_key_value_line():
    with pytest.raises(lint.FrontmatterError) as exc:
        lint.parse_frontmatter("---\ntitle: X\n  - nested\n---\n")
    assert exc.value.line == 3


def test_parse_frontmatter_rejects_unterminated_list():
    with pytest.raises(lint.FrontmatterError) as exc:
        lint.parse_frontmatter("---\nsources: [a.md\n---\n")
    assert exc.value.line == 2


def test_parse_frontmatter_rejects_unclosed_block():
    with pytest.raises(lint.FrontmatterError) as exc:
        lint.parse_frontmatter("---\ntitle: X\n")
    assert exc.value.line == 1


def test_iter_links_returns_relative_targets_only():
    text = "\n".join(
        [
            "See [a](../concepts/a.md) and [b](b.md#section).",
            "External [x](https://example.com/a.md), mail [m](mailto:me@x.org), anchor [s](#top).",
            "Inline `arr[0](i)` is code.",
            "```python",
            "f[0](x)",
            "```",
            'Spaced [c](my%20page.md "title").',
        ]
    )
    assert lint.iter_links(text) == [(1, "../concepts/a.md"), (1, "b.md"), (7, "my page.md")]


def make_root(path: Path) -> Path:
    (path / "raw").mkdir(parents=True)
    (path / "wiki" / "concepts").mkdir(parents=True)
    (path / "CLAUDE.md").write_text("# Wiki\n")
    (path / "index.md").write_text("# Index\n")
    return path


def test_find_root_walks_up_from_nested_dir(tmp_path):
    root = make_root(tmp_path / "w")
    assert lint.find_root(root / "wiki" / "concepts") == root.resolve()


def test_find_root_returns_none_outside_a_wiki(tmp_path):
    assert lint.find_root(tmp_path) is None


# --- link, index, orphan checks --------------------------------------------

SCRIPT = Path(lint.__file__).resolve()

NEW_PAGE = (
    "---\n"
    "title: New\n"
    "type: concept\n"
    "sources: [wiki/sources/blog-transformer-notes.md]\n"
    "updated: 2026-10-05\n"
    "---\n"
    "# New\n"
    "\n"
    "See [self-attention](self-attention.md).\n"
)


def codes(findings):
    return {(f.path, f.code) for f in findings}


def append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def test_clean_fixture_has_no_findings(wiki):
    assert lint.lint(wiki) == []


def test_broken_link_in_page(wiki):
    append(wiki / "wiki/concepts/self-attention.md", "\nSee [missing](../concepts/missing.md).\n")
    assert codes(lint.lint(wiki)) == {("wiki/concepts/self-attention.md", "broken-link")}


def test_broken_link_to_raw_file(wiki):
    append(wiki / "wiki/sources/tinyattn-1a2b3c4.md", "\n[gone](../../raw/pdf/gone.pdf)\n")
    assert codes(lint.lint(wiki)) == {("wiki/sources/tinyattn-1a2b3c4.md", "broken-link")}


def test_dangling_index_entry(wiki):
    append(wiki / "index.md", "- [Gone](wiki/concepts/gone.md) — removed page\n")
    assert codes(lint.lint(wiki)) == {("index.md", "index-dangling")}


def test_page_missing_from_index(wiki):
    (wiki / "wiki/concepts/new.md").write_text(NEW_PAGE, encoding="utf-8")
    append(wiki / "wiki/concepts/self-attention.md", "\nRelated: [new](new.md).\n")
    assert codes(lint.lint(wiki)) == {("wiki/concepts/new.md", "index-missing")}


def test_orphan_page_linked_only_from_index(wiki):
    (wiki / "wiki/concepts/new.md").write_text(NEW_PAGE, encoding="utf-8")
    append(wiki / "index.md", "- [New](wiki/concepts/new.md) — new page\n")
    assert codes(lint.lint(wiki)) == {("wiki/concepts/new.md", "orphan")}


def test_self_link_does_not_count_as_inbound(wiki):
    (wiki / "wiki/concepts/new.md").write_text(NEW_PAGE + "\n[me](new.md)\n", encoding="utf-8")
    append(wiki / "index.md", "- [New](wiki/concepts/new.md) — new page\n")
    assert codes(lint.lint(wiki)) == {("wiki/concepts/new.md", "orphan")}


def test_main_exit_codes(wiki, tmp_path, capsys):
    assert lint.main([str(wiki)]) == 0
    append(wiki / "wiki/concepts/self-attention.md", "\n[x](nope.md)\n")
    assert lint.main([str(wiki / "wiki")]) == 1
    assert "wiki/concepts/self-attention.md:" in capsys.readouterr().out
    empty = tmp_path / "empty"
    empty.mkdir()
    assert lint.main([str(empty)]) == 2


def test_runs_as_script_from_inside_wiki(wiki):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=wiki / "wiki", capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


# --- frontmatter checks ------------------------------------------------------

CONCEPT = "wiki/concepts/self-attention.md"
CODE_SRC = "wiki/sources/tinyattn-1a2b3c4.md"
CONCEPT_SOURCES = "sources: [wiki/sources/blog-transformer-notes.md, wiki/sources/tinyattn-1a2b3c4.md]"
SHA_LINE = "commit: 1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d\n"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def fm_messages(findings):
    return [(f.path, f.message) for f in findings if f.code == "frontmatter"]


@pytest.mark.parametrize(
    "path, old, new, expected",
    [
        (CONCEPT, "---\ntitle: Self-attention\n", "title: Self-attention\n", "missing frontmatter block"),
        (CONCEPT, "title: Self-attention\n", "", "missing field: title"),
        (CONCEPT, "updated: 2026-10-02\n", "updated:\n", "missing field: updated"),
        (CONCEPT, "type: concept", "type: entity",
         "type 'entity' does not match folder 'concepts' (expected 'concept')"),
        (CONCEPT, CONCEPT_SOURCES, "sources: wiki/sources/blog-transformer-notes.md",
         "sources must be an inline list like [a, b]"),
        (CONCEPT, CONCEPT_SOURCES, "sources: []", "sources must list at least one source page"),
        (CONCEPT, "wiki/sources/tinyattn-1a2b3c4.md]", "wiki/sources/nope.md]",
         "sources entry does not exist: wiki/sources/nope.md"),
        (CONCEPT, "updated: 2026-10-02", "updated: 02/10/2026",
         "updated is not a YYYY-MM-DD date: 02/10/2026"),
        (CONCEPT, "updated: 2026-10-02", "updated: 2026-13-45",
         "updated is not a YYYY-MM-DD date: 2026-13-45"),
        (CODE_SRC, "raw: raw/code/tinyattn-1a2b3c4.md\n", "", "missing field: raw"),
        (CODE_SRC, "origin: https://github.com/example/tinyattn\n", "", "missing field: origin"),
        (CODE_SRC, "raw: raw/code/tinyattn-1a2b3c4.md", "raw: raw/code/missing.md",
         "raw is not an existing file under raw/: raw/code/missing.md"),
        (CODE_SRC, SHA_LINE, "", "code source needs commit: <40-char SHA>"),
        (CODE_SRC, SHA_LINE, "commit: 1a2b3c4\n", "code source needs commit: <40-char SHA>"),
    ],
)
def test_frontmatter_problem_is_reported(wiki, path, old, new, expected):
    replace_once(wiki / path, old, new)
    assert (path, expected) in fm_messages(lint.lint(wiki))


def test_malformed_frontmatter_reports_parse_line(wiki):
    replace_once(wiki / CONCEPT, "type: concept\n", "type: concept\n  - nested\n")
    findings = [f for f in lint.lint(wiki) if f.code == "frontmatter"]
    assert [(f.path, f.line) for f in findings] == [(CONCEPT, 4)]


def test_page_outside_type_folder(wiki):
    (wiki / "wiki/stray.md").write_text(NEW_PAGE, encoding="utf-8")
    assert ("wiki/stray.md", "page must live in a type folder under wiki/") in fm_messages(lint.lint(wiki))


def test_extra_type_folder_accepts_its_own_type(wiki):
    (wiki / "wiki/benchmarks").mkdir()
    (wiki / "wiki/benchmarks/mmlu.md").write_text(
        NEW_PAGE.replace("type: concept", "type: benchmark"), encoding="utf-8"
    )
    assert fm_messages(lint.lint(wiki)) == []


# --- raw immutability ----------------------------------------------------------

RAW_WEB = "raw/web/blog-transformer-notes.md"
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd, check=True, capture_output=True,
    )


def commit_all(repo: Path) -> None:
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Seed")


def test_no_git_repo_means_no_raw_findings(wiki):
    append(wiki / RAW_WEB, "edited\n")
    assert lint.lint(wiki) == []


@needs_git
def test_committed_raw_is_clean(wiki):
    commit_all(wiki)
    assert lint.lint(wiki) == []


@needs_git
def test_modified_raw_file_is_reported(wiki):
    commit_all(wiki)
    append(wiki / RAW_WEB, "edited\n")
    assert codes(lint.lint(wiki)) == {(RAW_WEB, "raw-modified")}


@needs_git
def test_new_untracked_raw_file_is_allowed(wiki):
    commit_all(wiki)
    (wiki / "raw/web/new.md").write_text("new capture\n", encoding="utf-8")
    assert lint.lint(wiki) == []


@needs_git
def test_wiki_inside_larger_repo_reports_wiki_relative_path(wiki):
    commit_all(wiki.parent)
    append(wiki / RAW_WEB, "edited\n")
    assert codes(lint.lint(wiki)) == {(RAW_WEB, "raw-modified")}


@needs_git
def test_staged_new_raw_file_is_allowed(wiki):
    commit_all(wiki)
    (wiki / "raw/web/new.md").write_text("new capture\n", encoding="utf-8")
    git(wiki, "add", "raw/web/new.md")
    assert lint.lint(wiki) == []


@needs_git
def test_non_ascii_raw_path_is_reported_verbatim(wiki):
    name = "raw/web/한글-노트.md"
    (wiki / name).write_text("원본\n", encoding="utf-8")
    commit_all(wiki)
    append(wiki / name, "edited\n")
    assert codes(lint.lint(wiki)) == {(name, "raw-modified")}


@needs_git
def test_deleted_raw_file_is_reported(wiki):
    commit_all(wiki)
    (wiki / RAW_WEB).unlink()
    assert (RAW_WEB, "raw-modified") in codes(lint.lint(wiki))


# --- crash handling -------------------------------------------------------------


def test_undecodable_page_reports_only_one_frontmatter_finding(wiki):
    (wiki / CODE_SRC).write_bytes(b"\xff\xfe bad")
    [finding] = lint.lint(wiki)
    assert (finding.path, finding.line, finding.code, finding.message) == (
        CODE_SRC, 1, "frontmatter", "file is not valid UTF-8"
    )


def test_main_returns_3_when_lint_itself_fails(wiki, capsys):
    (wiki / "index.md").write_bytes(b"\xff\xfe bad")
    assert lint.main([str(wiki)]) == 3
    assert capsys.readouterr().err.startswith("lint.py: error: ")


def test_source_page_must_link_to_its_raw_file(wiki):
    page = "wiki/sources/blog-transformer-notes.md"
    replace_once(wiki / page, "Raw: [blog-transformer-notes](../../raw/web/blog-transformer-notes.md)\n", "")
    assert fm_messages(lint.lint(wiki)) == [
        (page, "source page does not link to its raw file: raw/web/blog-transformer-notes.md")
    ]
