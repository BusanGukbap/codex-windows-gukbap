---
name: brainstorming
description: Use to resolve meaningful design uncertainty in substantial work. Skip simple questions and clear small changes; do not repeat approval for already authorized work.
---

# Brainstorming Ideas Into Designs

Understand the user's outcome before choosing an implementation. Keep thecasterian's design-first approach proportional to the task.

## Scope first

Read the relevant existing files and conventions before proposing changes. Do not turn a clear request into an interview.

- A small, clear change: state any material assumption and proceed with focused verification.
- A substantial request with enough constraints: present a concise design and implementation sequence, then continue within the authorized scope.
- A choice that materially changes the product, risk, or cost: ask one targeted question. Continue independent work while awaiting the answer when possible.

Ask for a design decision when the user must choose; do not require a second approval merely because a document was written.

## Explore the design

1. State the concrete problem, intended user, success criteria, and relevant constraints.
2. Compare genuinely different viable approaches when a choice remains. Explain the trade-off and recommend one.
3. Cover components, data flow, errors, security boundaries, and verification only to the depth the work requires.
4. Keep the smallest design that meets the goal. Preserve existing architecture unless the requested change requires otherwise.
5. For larger work, save one concise design or plan in the project's established location. Do not create duplicate spec/plan/log artifacts.

If the user redirects the work, incorporate the correction. Stop only dependent work when clarification is needed.

## Visual companion

Offer the optional visual companion only when a visual decision benefits from it. Use [visual-companion.md](visual-companion.md) after the user requests or accepts it. Windows entrypoints are `python scripts/start-server.py` and `python scripts/stop-server.py`; Node.js is required for the server.

## Handoff

Use writing-plans when the design needs a durable multi-step execution plan. Otherwise implement the authorized change directly.

Do not commit, push, create a pull request, deploy, or install into live user configuration without the required explicit authorization. Completing a design is not permission to publish it.
