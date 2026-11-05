# Personal Windows and Codex adaptation

Status: completed

Goal: make the user's fork usable locally on native Windows with Codex, preserving thecasterian's useful skills and the user's lightweight workflow rules.

Constraints: no commits, pushes, PRs, remote contributions, live profile replacement, dependency installation, or permission/trust bypasses. Preserve original Claude assets as reference where a Codex equivalent differs.

## Work

- [x] Adapt active skills and prompts to available Codex tools and portable commands.
- [x] Port executable helper paths to Python/Node on native Windows, with focused tests.
- [x] Add a read-only-by-default personal installer, backup/replace controls, duplicate detection, and optional guidance merging.
- [x] Document migrated features and manual/optional integrations.
- [x] Validate an isolated Unicode/space-containing profile, helpers, final diff, and publication state.

Validation: installer/helper unittest suites; native Node visual companion smoke test; static instruction scan; independent review of installer path safety and scope. No repeated checks without relevant changes.

## Evidence and limits

- Installer: `python -m unittest discover -s tests -p test_install.py -v` passed 12 tests. After the cross-platform symlink cleanup correction, only `-k linked_profile` was rerun and passed.
- Helpers: `python -m unittest discover -s tests -p test_helpers.py -v` passed 11 tests. After process-permission handling was strengthened, the two affected tests passed again. Includes forced cp949 IO, Korean/emoji paths, actual Node HTTP authentication, native Windows process identity checks, and start/stop cleanup.
- `node --check skills/writing-skills/render-graphs.js` passed. Node/CIM checks required approved execution outside the restricted sandbox; no application workaround was added.
- Final isolated integration installed all 16 skills and 73 resource files with optional guidance. Installed bytes matched the source, and a second preview reported zero changes. Real-profile preview reported 30 changed / 44 unchanged files; no live install was performed. Existing global AGENTS.md, config.toml, and hooks.json fingerprints remained unchanged.
- Active skill headers and links were checked; `git diff --check` passed. Independent reviews found and closed UTF-8 input/output, non-mutating help, process identity uncertainty, and test link-cleanup issues.
- Graphviz and clang-format binaries are absent: their adapters were checked with mocks, not real formatting/rendering. Legacy Claude shell hooks/statusline remain reference assets; optional Codex hook registration and trust are manual.
- Source revision remains `4fa4ebd040e5b3aae0ad105fb6b39e3e4322000e`. All implementation changes are local and uncommitted; no push, PR, or upstream contribution occurred.

Resume point: local adaptation is complete. Review README-CODEX.md and run the default installer preview before deciding whether to apply to the personal profile. Do not infer approval for live installation or Git publication from this completed conversion task.

## Separately authorized personal publication

After the conversion was completed, the user explicitly selected a new private repository named `BusanGukbap/codex-windows-gukbap` for committing and pushing this version on `main`. This later authorization covers personal publication only; upstream contributions and live-profile installation remain outside its scope. The README now identifies the personal destination. Runtime files and their successful test evidence are unchanged.
