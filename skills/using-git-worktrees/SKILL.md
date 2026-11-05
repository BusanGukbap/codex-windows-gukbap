---
name: using-git-worktrees
description: Use when implementation needs isolation from an existing checkout or the user requests a worktree. Reuse an already isolated checkout.
---

# Using Git Worktrees

Protect unrelated changes while keeping the workspace arrangement simple.

## Detect existing isolation

Use Git directly through the available Codex command tool:

```powershell
git rev-parse --show-toplevel
git rev-parse --git-dir
git rev-parse --git-common-dir
git rev-parse --show-superproject-working-tree
git branch --show-current
git status --short
```

Different Git/common directories may indicate a linked worktree or submodule; check the superproject output before deciding. A fresh clone or already isolated checkout does not need another worktree.

## Choose an isolation method

1. Follow the user's workspace preference.
2. Reuse an appropriate existing isolated checkout.
3. Use a native Codex worktree tool when available and authorized.
4. Otherwise use Git's worktree command if isolation is needed.

Do not silently change the working directory of another chat. For a small safe edit, work directly in the current checkout when it does not disturb unrelated work.

For a project-local `.worktrees` directory, verify it is ignored. If an ignore rule is needed, make the minimal authorized edit; do not commit it automatically.

```powershell
git check-ignore .worktrees
git worktree add ".worktrees/my-task" -b "codex/my-task"
```

Quote complete paths. Before recursive deletion or moving any workspace on Windows, verify its resolved absolute path is the intended target, and use native PowerShell operations. Never combine path enumeration with a second shell's deletion command.

## Setup and verification

Inspect the project's existing commands. Use installed dependencies first; do not install packages or change build configuration merely because a conventional manifest exists.

Reuse valid baseline results. Run focused checks relevant to the change; broaden verification for actual risk. Distinguish pre-existing failures from failures introduced by the task.

## Cleanup

Preserve the workspace until the user requests removal or an explicitly authorized workflow owns it. Never discard unrelated changes. Do not remove host-managed worktrees with a manual Git command.

Git commits, pushes, PRs, and merges still require separate explicit authorization.
