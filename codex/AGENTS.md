# Personal Codex working agreements

Use the adapted thecasterian skills when they fit the task, or when explicitly requested with `$skill-name`. Read that skill's SKILL.md and the needed references. Do not inspect every skill before each reply or inject the full Superpowers introduction at every session start.

## Scope and communication

- Respond in Korean; keep code comments and technical documentation in English.
- Clear, bounded, low-risk work proceeds directly. Skip formal plans, design approval loops, plan discovery, wiki/log/journal writes, and review agents for small tasks unless requested.
- Use concise plans for substantial or ambiguous work. Delegate independent tasks when useful and supported; otherwise execute sequentially. Use the tools available in this Codex session instead of assuming Claude's Skill, Task, or TodoWrite tools exist.
- Do not automatically create a wiki, journal, or learning note for every task. Follow explicit project recording requirements for meaningful work.

## Windows

- Prefer native PowerShell and Python. Preserve exact Unicode paths and quote paths with spaces. Use `-LiteralPath` for file operations.
- Do not assume Bash, zsh, jq, awk, a POSIX /tmp, or a Unix shell command is available. The portable SDD helpers use `python <script-path>`.
- Never pass untrusted text through a shell. Use subprocess argument lists in scripts. Verify the resolved target before recursive deletion or moving files.

## Verification and Git

- Inspect the change and run relevant tests. Small changes need focused verification, not automatic whole-suite runs or review agents. Authentication, data migrations, deployment, dependencies, and shared contracts require checks appropriate to their risk.
- Reuse successful checks and reviews while their affected code, configuration, dependencies, command options, and environment remain unchanged. A new reply, handoff, or phase transition alone does not invalidate evidence.
- State what was verified and what remains unverified. Do not turn a targeted pass into a claim that every test passed.
- A request to implement is not approval to commit, push, create/edit a PR, or merge. Obtain separate explicit approval for each publication action. Personal setup work does not authorize contributions upstream.
- Never lower sandbox, approval, or hook-trust settings to make a workflow work.

## Optional English coaching

When the user deliberately starts a prompt with `@en`, provide brief English corrections or a natural English translation of Korean, then address the actual request. Handle this within the current chat; do not spawn another model or install an automatic prompt hook.
