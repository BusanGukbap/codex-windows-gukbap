---
name: verification-before-completion
description: Use before reporting a change as complete to check that the evidence covers the current scope. Reuse valid results for unchanged inputs.
---

# Verification Before Completion

Evidence before claims. Report what was actually checked, with its practical limits.

## Choose checks by impact

1. Small, bounded, low-risk edits: inspect the diff and run only a focused check needed for the change. Do not run a full suite, broad E2E checks, or reviewer agents unless explicitly requested.
2. Normal behavior changes: run affected tests and relevant lint/type/build checks. Expand only when shared behavior, a failure, or a concrete unresolved concern justifies it.
3. High-risk or cross-cutting changes: use the relevant integration/E2E or full-suite checks and one independent review appropriate to the risk. Authentication, data migrations, public contracts, deployment, dependencies, and build changes do not become small merely because the diff is short.

Preserve required CI/release gates and security checks.

## Reuse evidence

A successful command or review remains evidence while its covered source, configuration, dependencies, environment, and command/options are unchanged. Check that the evidence covers the final diff.

- Re-run only affected checks after a relevant change, failure, incomplete result, new symptom, unreliable evidence, or an explicit user request.
- A completion reply, handoff, new phase, or commit/PR preparation alone is not a reason to re-run checks.
- Read actual command output and review findings. An agent saying "done" without evidence is insufficient.
- Reuse a review of the same scope across workflow gates. Do not spawn another reviewer solely for a different gate name.
- Stop after required checks pass; do not broaden testing without new evidence.

## Report accurately

State the command, result, and scope. A targeted test pass is not a full-suite pass. A code change without a reproduction check is not proof that the original bug is fixed.

If verification is unavailable or fails, say what remains unverified and why. Do not infer success.

For substantial planned work, update existing progress state as needed. Small edits do not require plan/log artifacts.

Commit, push, PR, merge, and deployment actions remain separately authorized actions; successful verification does not grant that authorization.
