---
name: requesting-code-review
description: Use for an explicitly requested review or a substantial/risky change that warrants independent review. Skip review agents for small edits.
---

# Requesting Code Review

Give a reviewer the smallest complete context needed to assess the change.

## When to review

Use one independent review for a major or high-risk change, before an approved merge when required, or when the user explicitly asks. Small scoped edits do not need a reviewer agent.

Reuse an existing review while the reviewed scope and relevant inputs are unchanged. A task, evaluator, and final gate can share that review. Do not ask a reviewer to re-run successful checks without a concrete concern.

## Prepare the review input

- State the problem, expected behavior, constraints, and verification evidence.
- For committed work, record the actual base/head revision covering the full task, not blindly HEAD~1.
- For uncommitted work, provide the working-tree diff and list untracked files to inspect explicitly. Do not make a commit merely to enable a review.
- Supply the prompt at [code-reviewer.md](code-reviewer.md).
- Use available Codex collaboration tools with read-only file ownership. If unavailable, perform the same focused review inline and report that limitation.

Example read-only Windows commands:

```powershell
git status --short
git diff --no-ext-diff --stat HEAD
git diff --no-ext-diff -U10 HEAD
git ls-files --others --exclude-standard
```

The diff commands omit untracked file contents; read relevant new files separately.

## Handle findings

Fix correctness/security issues within the authorized scope. Re-run checks covering the fix; unrelated successful checks remain evidence. Note lower-priority findings without silently expanding the task.

A review is not approval to commit, push, open a PR, or merge.
