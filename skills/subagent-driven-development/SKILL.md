---
name: subagent-driven-development
description: Use for substantial implementation plans with independent tasks when Codex collaboration tools are available. Small edits stay inline.
---

# Subagent-Driven Development

Execute substantial independent tasks with focused ownership and evidence. Preserve thecasterian's isolation and handoff discipline without duplicating reviews.

## Preconditions

- Read the plan's requirements, global constraints, and shared interfaces.
- Use this workflow only when delegation saves time or improves quality.
- Use available Codex collaboration tools. If they are unavailable or tasks are tightly coupled, execute inline with executing-plans.
- Small scoped fixes skip plan/log artifacts, full suites, and review agents unless explicitly requested.
- Keep the user's selected model/settings; do not force a different model or service tier.

## Dispatch an implementer

For each independent task, assign explicit file/module ownership and tell the worker that others may be editing the checkout: do not revert their changes.

Give the worker its task, required interfaces, relevant constraints, and expected report. Avoid copying the whole session history. A task brief can be extracted with the portable helper:

```powershell
python "<skill-directory>/scripts/task-brief" "<plan-file>" 1
```

Read the helper's reported path. It is the worker's requirements; do not paraphrase exact values into conflicting copies.

The worker reports:
- DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
- Files changed and resulting behavior.
- Actual verification commands/results and unverified scope.
- A concise list of concerns.

No worker may commit, push, open a PR, merge, or publish unless the user separately approved that action. A task can be complete with uncommitted changes.

## Verify and review

Inspect actual changes and evidence; a worker's unsupported success claim is insufficient.

- Run only affected checks after a relevant change or failure.
- Use one independent review when risk warrants it or the user requests it.
- Supply the task's requirements, implementation report, and relevant diff to [task-reviewer-prompt.md](task-reviewer-prompt.md).
- Reuse the same review across task, evaluator, and final gates when its scope covers them.
- Do not demand another whole-branch reviewer for an already reviewed unchanged scope.

For a committed range, the review package helper produces one file:

```powershell
python "<skill-directory>/scripts/review-package" "<base-revision>" "<head-revision>"
```

For uncommitted changes use `git diff --no-ext-diff -U10 HEAD` plus `git ls-files --others --exclude-standard`, and supply relevant untracked files separately. Do not commit to manufacture a review range.

## Resolve problems

Provide missing context or fix a concrete concern instead of retrying unchanged work. Batch related findings into one fix assignment. Re-review only the changed or previously unresolved scope.

Pause dependent work for a genuinely blocking design decision; continue independent authorized tasks. Do not ask whether to continue between tasks already covered by the request.

## Durable progress

For a long-running plan, use the project's existing ledger or `.superpowers/sdd/progress.md`. Record completed outcomes, file paths, and check evidence; record commit IDs only when commits actually exist. Do not automatically resume an unrelated old task.

The optional workspace helper is portable:

```powershell
python "<skill-directory>/scripts/sdd-workspace" --help
```

Use the helper's documented commands; it never grants permission to publish. Preserve the checkout and finish with a concise result, verification scope, and remaining concerns.

## Prompt templates

- [implementer-prompt.md](implementer-prompt.md)
- [task-reviewer-prompt.md](task-reviewer-prompt.md)
- [code-reviewer.md](../requesting-code-review/code-reviewer.md)
