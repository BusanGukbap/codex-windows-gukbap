---
name: finishing-a-development-branch
description: Use after implementation to report verified local work or carry out a Git integration action explicitly requested by the user.
---

# Finishing a Development Branch

Finish the requested work with clear evidence and a preserved checkout.

## Default: keep local work

1. Inspect the final diff and the required verification evidence.
2. Reuse passing results for unchanged relevant inputs. Do not repeat tests solely to finish the workflow.
3. Report changed behavior, the verification scope, material limitations, and the checkout path.
4. Leave the working tree and branch intact.

Do not require a merge/PR/discard menu when the user only requested implementation.

## Approved integration actions

A coding request does not imply approval to commit, push, merge, or create/edit a PR. Before asking for such approval, prepare a concrete reviewable diff and summarize its behavior and verification.

Approval is scoped to the described diff and action:

- Commit approval covers committing that diff, not pushing it.
- Push approval names the branch and does not authorize a PR.
- A PR or merge requires its own explicit request.
- "Personal use" or "do not contribute" means keep work local and do not publish to the fork or upstream.

Only execute an action after its relevant approval. Follow the user's commit-message conventions; do not add a co-author automatically.

## Workspace cleanup

Keep worktrees and local files unless removal was requested or is part of an explicitly authorized owned cleanup. Before a destructive operation, show the exact target and impact and obtain any required approval.

On Windows use resolved, quoted absolute paths and native PowerShell file operations. Do not build cross-shell recursive delete commands. Use native Codex worktree management for host-managed workspaces.

A failed check blocks a success claim, not independent investigation or repair. Explain unresolved failures accurately instead of claiming completion.
