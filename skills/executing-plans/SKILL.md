---
name: executing-plans
description: Use to execute an approved substantial implementation plan inline, including when subagent tools are unavailable or tasks are tightly coupled.
---

# Executing Plans

Read the plan, resolve material gaps, execute the authorized tasks, and report the evidence.

## Execution

1. Read the plan once and check success criteria, constraints, ownership, and verification methods.
2. Ask only about ambiguity that prevents a correct implementation. Continue independent work where possible.
3. Track substantial tasks with the available Codex plan tool or the project's existing progress file.
4. Execute each task and run its focused checks. Reuse results whose relevant inputs remain unchanged.
5. Continue without repeated "should I continue" check-ins while the next task is within the existing authorization.

If independent tasks benefit from collaboration and Codex subagent tools are available, use subagent-driven-development. Otherwise work inline; do not invent tool APIs or require a separate user chat.

## Completion

Use verification-before-completion to assess evidence. Then use finishing-a-development-branch only for the completion/integration behavior needed by the task. An existing valid review can satisfy the final gate; it does not need another reviewer.

Small tasks bypass this workflow's plan/log/review artifacts. Git commits, pushes, pull requests, and merges require separate explicit approval.

## Re-plan when necessary

If the approach is invalid or a blocker prevents progress, explain the concrete issue, investigate, and update the plan. Do not keep retrying the same failed action, and do not stop independent authorized work merely because one part needs user input.
