# Lint

Report problems, then fix only what the user approves.

## 1. Mechanical checks

Run `python3 <this skill's base directory>/scripts/lint.py <wiki-root>`. Exit 0 = clean, 1 = findings, 2 = no wiki found, 3 = lint itself failed (report the stderr message; it is not a finding).

| Code | Meaning | Usual fix |
|---|---|---|
| `broken-link` | A link in a wiki page points to a missing file | Correct the path or remove the link |
| `orphan` | No other wiki page links to this page | Link it from the most related page |
| `index-missing` | Page not listed in `index.md` | Add its index line |
| `index-dangling` | `index.md` links to a missing page | Remove or correct the line |
| `frontmatter` | Missing or invalid field | Fix the field per SKILL.md |
| `raw-modified` | A tracked raw file was edited | Restore it with `git -C <wiki-root> checkout -- <path>`; ingest a changed source as a new raw file |

## 2. Judgment checks

- **Unresolved conflicts:** list every `> **Conflict:**` note with a suggested resolution or a source that would settle it.
- **Stale code:** for each `raw/code/*.md`, compare its `commit:` with `git ls-remote -- "<origin>" HEAD`, only for the current manifest per origin (the one whose source page no other source page lists as superseded); superseded manifests are history, not stale. List the differing repos and the pages that cite them.
- **Missing pages:** terms mentioned on 3 or more pages that have no page of their own.
- **Thin pages:** entity or concept pages whose `sources:` has a single entry.

## 3. Report and fix

Show one report grouped by section 1 code and section 2 check. Ask which fixes to apply; the mechanical fixes may be approved as one batch. Apply only approved fixes, rerun `lint.py`, and append `## [YYYY-MM-DD] lint | <summary of fixes>` to `log.md`.

If `git -C <wiki-root> rev-parse --is-inside-work-tree` prints `true` and `git -C <wiki-root> rev-parse --show-toplevel` is not `$HOME`:
`git -C <wiki-root> add -- . && git -C <wiki-root> commit -m "Lint wiki" -- .`
