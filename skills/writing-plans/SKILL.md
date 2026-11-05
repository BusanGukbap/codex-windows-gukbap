---
name: writing-plans
description: Use when substantial multi-step work needs a durable implementation plan. Skip planning artifacts for clear small tasks.
---

# Writing Plans

Write a plan that a capable implementer can execute without reconstructing the conversation. Follow the project's established plan location; otherwise use `docs/plans/YYYY-MM-DD-topic.md`.

## Plan content

- Goal and observable success criteria.
- Constraints, non-goals, and the files/interfaces affected.
- A short sequence of independently verifiable tasks.
- Relevant verification commands and what their results prove.
- Known decisions, assumptions, and stopping conditions.

Scale detail to uncertainty and risk. Do not transcribe the whole implementation into the plan or require a separate reviewer per trivial step.

## Task structure

```markdown
### Task N: Concrete outcome

Files: path/to/implementation, path/to/relevant-test
Requirements: resulting behavior and important edge cases
Steps:
- Inspect the connected code and existing conventions.
- Add a meaningful regression test or focused check when behavior warrants it.
- Make the smallest complete change.
- Run the affected checks and report the actual result.

Done when: observable success criteria and verification scope
```

Use current documented APIs and existing dependencies. Shell commands for Windows must use PowerShell or portable Python/Node/Git commands; quote Unicode paths.

## Execution

Choose subagent-driven-development for substantial independent tasks when Codex collaboration tools are available. Assign file ownership, explain that other workers may be editing the checkout, and supply focused context. Use executing-plans inline when tasks are coupled or agents are unavailable.

A plan authorizes only the work already requested by the user. Commit, push, pull request, merge, and deployment actions require their own explicit approvals. Do not add automatic commit steps.

## Verification discipline

Reuse valid check/review results for unchanged relevant inputs. Small edits get focused checks; broader tests and one independent review are reserved for risk that warrants them. A status update or phase transition does not invalidate existing evidence.
