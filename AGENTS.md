# Personal Windows and Codex adaptation

This local checkout adapts thecasterian/claude-code through the user's BusanGukbap/claude-code-steal fork for personal use.

- Do not commit, push, open a PR, or contribute to either repository without a new explicit request. Keep upstream attribution.
- Use native PowerShell and Python on Windows. Normal setup must not require Bash, WSL, jq, awk, or a new package installation.
- Keep changes focused on Codex compatibility. Historical Claude files are reference material, not Codex permissions or hook configuration.
- Preserve the user's existing global guidance, plugins, credentials, and unrelated skills. Installer defaults must preview changes without writing anything.
- Reuse an existing unique skill installation instead of creating a second registration. Refuse ambiguous duplicates and path links before writing.
- Small tasks skip formal plans, journals, wiki updates, whole-suite checks, and review agents. Larger changes use focused checks appropriate to their impact; reuse passing evidence for unchanged code and environment.
- Use `python -m unittest discover -s tests` for the new portable setup tests. Optional helpers may require Node, Git, Graphviz, or clang-format; report which were actually tested.
- Responses are Korean. Code comments and technical documentation are English. Report incomplete scope honestly.

See README-CODEX.md for personal installation and docs/plans/2026-11-06-personal-windows-codex.md for scope and validation.
