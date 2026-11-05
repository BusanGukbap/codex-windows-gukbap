# Personal Windows and Codex setup

This is a personal adaptation of [thecasterian/claude-code](https://github.com/thecasterian/claude-code), via [BusanGukbap/claude-code-steal](https://github.com/BusanGukbap/claude-code-steal), starting from revision `4fa4ebd040e5b3aae0ad105fb6b39e3e4322000e`. Original authorship and reference material are preserved. Personal changes live in the private [BusanGukbap/codex-windows-gukbap](https://github.com/BusanGukbap/codex-windows-gukbap) repository; neither upstream nor the original fork is updated.

## Requirements

- Native Windows PowerShell and Python 3.11+ on PATH for installation and portable helpers.
- Git for worktrees and SDD review packages.
- Node.js for the optional visual companion; Graphviz `dot` for optional graph rendering; `clang-format` for optional C/C++ formatting.
- No WSL, Git Bash, jq, awk, additional Python packages, or API key is needed for normal installation. Optional tools are not downloaded by the installer.

## Preview first

Open PowerShell in this checkout:

```powershell
python .\scripts\install.py
```

The default only prints a plan. It does not change your skills, configuration, plugins, hooks, or guidance.

To exercise installation in an isolated profile first:

```powershell
python .\scripts\install.py --home "$env:TEMP\Codex personal test" --apply
```

An explicit `--home` isolates the profile from an inherited `CODEX_HOME`. To select a different Codex configuration directory intentionally, pass `--codex-home` as well. Without `--home`, the installer honors `CODEX_HOME`.

After reviewing the real-profile preview, the explicit installation command is:

```powershell
python .\scripts\install.py --apply --replace --with-guidance
```

`--replace` authorizes replacing differing managed files, after backup. `--with-guidance` installs the optional personal guidance fragment. Omit it to keep your existing global AGENTS.md unchanged. Existing guidance outside the clearly delimited managed block is preserved. The installer prints its backup location; keep that backup if you want to restore earlier files.

## Skill locations and duplicates

The installer reuses each skill's existing unique directory in either `~/.codex/skills` (including a custom `CODEX_HOME`) or `~/.agents/skills`. New skills use `~/.agents/skills`. If the same name exists in both locations, installation stops before writing: choose which existing installation to keep first. Unrelated skills and extra user files are preserved.

Keep the official Superpowers plugin uninstalled when using this personal version to avoid duplicate skill selectors. This installer does not alter plugin installation state or globally enable/disable skills. Review existing `skills.config` overrides separately if a skill does not appear.

Restart Codex after installing. Invoke a skill explicitly with `$brainstorming`, `$systematic-debugging`, or another installed skill name. Plain chat and small changes do not need the full skill workflow. See [Codex skills](https://learn.chatgpt.com/docs/build-skills) and [AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Optional frequently used personal skills

`personal-skills/` contains 6 snapshots explicitly selected by the user: `i-have-adhd`, `gh`, `archify`, `find-docs`, `drawio-skill`, and `graphify`. A bounded usage audit informed the initial shortlist; the final set is the user's choice. The sample covers 17 root chats from 2026-10-27 through 2026-11-06 (KST), excludes the current maintenance chat, and counts concrete SKILL.md read calls rather than catalog mentions. These are observed loads, not proof that every invocation was deliberate. Existing core skills are not duplicated here.

| Use | Included snapshots |
| --- | --- |
| Response style | `i-have-adhd` |
| Documentation and GitHub | `find-docs`, `gh` |
| Code knowledge graphs | `graphify` |
| Diagrams | `archify`, `drawio-skill` |

Selection counts, source identifiers, licenses, resource sizes, compatibility notes, and source hashes are recorded in [the snapshot manifest](codex/personal-skills.json). Original skill content and bundled license/reference files are preserved. No conversation histories or vault notes are included.

Preview this optional collection along with the 16 core skills:

```powershell
python .\scripts\install.py --with-personal-skills --with-guidance
```

After reviewing that preview, add `--apply --replace` to install explicitly. Without `--with-personal-skills`, the core-only default is unchanged. The same existing-location reuse, duplicate refusal, backup, and guidance-preservation rules apply.

These additional skills are source snapshots, not a promise that every external integration has been ported or tested on Windows. Some require connected MCP tools, Context7, a local knowledge-search service, Node, draw.io, or other separately installed software. Their upstream instructions may contain POSIX commands, platform-specific paths, broad auto-invocation rules, or separate permission prompts. Follow the current user/project policies and adapt only the needed command; do not install tools or run an entire workflow merely because a snapshot mentions it. Selecting this optional collection can affect skill routing after installation. No additional packages, services, plugins, or live settings are changed by previewing it.

## What was adapted

| Original integration | Windows/Codex behavior |
| --- | --- |
| Claude `Skill`, `Task`, and `TodoWrite` instructions | Codex skill invocation and available planning/delegation tools, with a sequential fallback |
| Bash SDD helpers | Native Python entrypoints, including Unicode and space-containing paths |
| Bash visual companion start/stop scripts | Native Python wrappers around the existing Node server |
| Shell test-polluter helper | Native Python helper; test commands execute as argument lists |
| Unix Graphviz detection | Cross-platform Node subprocess calls |
| SessionStart full-skill injection | Not installed; Codex already discovers skill metadata |
| English-correction subprocess hook | Optional `@en` behavior in personal guidance, handled in the current chat |
| C/C++ formatting hook | Native Python script, optional manual hook registration |
| Claude permissions, plugins, and custom shell status line | Kept as reference; not imported into Codex or used to lower permissions |
| Wiki `CLAUDE.md` schema files | Kept as wiki schema documents explicitly read by Codex; not blindly renamed |

The `.sh` files, `CLAUDE.md`, and `settings.json` remain upstream reference material. Active Codex instructions use the portable entrypoints. Skill references that teach another language or document upstream behavior are not executable Windows setup instructions.

## Portable helpers

Run from the checkout; after installation use the corresponding installed skill directory:

```powershell
python .\skills\subagent-driven-development\scripts\sdd-workspace
python .\skills\subagent-driven-development\scripts\task-brief .\docs\my-plan.md 1
python .\skills\subagent-driven-development\scripts\review-package BASE HEAD
python .\skills\brainstorming\scripts\start-server.py --project-dir .
```

Replace `BASE` and `HEAD` with actual reviewed Git revisions. Review packages describe committed ranges; they do not grant permission to commit. Use `git diff` to inspect uncommitted work. The visual companion is optional: approve opening a browser separately and stop its session using `stop-server.py` when done.

## Optional C/C++ formatting hook

`hooks/clang-format/post-tool-use.py` reads a Codex tool event as JSON from stdin. It requires an applicable `.clang-format`, limits paths to the event's working directory, and invokes `clang-format` without a shell. `clang-format` must already be on PATH.

To print a hook entry using this checkout's actual absolute path:

```powershell
$formatter = (Resolve-Path -LiteralPath '.\hooks\clang-format\post-tool-use.py').Path
@{
  hooks = @{
    PostToolUse = @(@{
      matcher = '^(apply_patch|Write|Edit)$'
      hooks = @(@{
        type = 'command'
        command = "python3 `"$formatter`""
        commandWindows = "python `"$formatter`""
        timeout = 10
      })
    })
  }
} | ConvertTo-Json -Depth 8
```

This prints JSON only. Review and merge it into your own `~/.codex/hooks.json` if you want automatic formatting. Preserve existing entries and register the formatter only once: Codex combines matching hook sources instead of replacing them. Review and trust the hook through Codex; do not bypass trust. The checkout must remain at that path, or the hook path must be updated. See the [official hooks documentation](https://learn.chatgpt.com/docs/hooks).

## Validation

```powershell
python -m unittest discover -s tests -v
```

These tests cover the new installer and native helpers, including isolated profiles and paths with spaces/Unicode. They do not prove every installed skill will be automatically selected by every Codex client. A real profile installation, host hook trust, API-backed English analysis, and optional external tools require separate checks when actually enabled.
