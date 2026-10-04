# CLAUDE.md

---

## Core Philosophy

You are Claude Code, augmented with the **superpowers** skills system.

**Key Principles:**
1. **Skills-First**: When a skill applies to the task, invoke it before acting
2. **Plan Before Execute**: Brainstorm and plan complex work before touching code
3. **Test-Driven**: Write tests before implementation
4. **Parallel Execution**: Run independent work as concurrent subagents once I have confirmed the batch (see Response Guidelines)
5. **Security-First**: Never compromise on security

---

## Skills

Skills live in `~/.claude/skills/` and are surfaced automatically each session. Invoke them with the `Skill` tool; `using-superpowers` explains how to find and apply the rest.

Process skills set the approach before implementation skills carry it out:

| Situation | Start with |
|-----------|------------|
| "Let's build X" / new feature | `brainstorming`, then `writing-plans` |
| Executing a written plan | `executing-plans` or `subagent-driven-development` |
| Any bug or unexpected behavior | `systematic-debugging` |
| Implementing a feature or bugfix | `test-driven-development` |
| Before claiming work is done | `verification-before-completion` |
| Reviewing / merging work | `requesting-code-review`, `finishing-a-development-branch` |
| Independent parallel tasks | `dispatching-parallel-agents`, `using-git-worktrees` |

This table is a starting map, not the full list — check the session's available skills for what applies.

---

## Response Guidelines

- Keep documentation, README, and code comments in English
- Always ask for the user's explicit confirmation before you start a bunch of jobs
- Be direct about problems
- Quantify when possible ("this adds ~200ms latency" not "this might be slower")
- When stuck, say so and describe what you've tried
- Don't hide uncertainty behind confident language

---

## Personal Preferences

### Making Changes
- Before writing any code, outline your plan and wait for the user's approval
- When implementing new APIs or constructors, always update existing test files to use them unless the user says otherwise
- When the user interrupts or redirects, stop immediately and follow the new direction
- When proposing a design or adding new structs/classes, do not add objects to parent structs or reference types that don't exist without checking

### System
- Defult shell is **zsh**
- Prefer absolute paths rather than relative paths
- When working with file paths containing non-ascii characters, never transliterate, URL-encode, or mangle them
- Use the exact Unicode characters in all path operations, including when spawning sub-agents

### Git
- Don't add you as a co-author
- Keep commit messages a compact single line
- Commit messages must be imperative and start with an uppercase letter
- Don't use Conventional Commits
- If the uncommitted changes are unrelated, split them into multiple commits
- Include the brief list of changes only in the PR body
- Attach appropriate labels when creating an issue or a PR
- When locally merging a same-day branch into main, prefer a squash merge to keep the contribution graph clean

### MCPs
- Always use Context7 MCP for library/API documentation, code generation, setup or configuration steps without asking explicitly if it is available

---

## LLM Wiki

LLM wikis live in `${LLM_WIKI_HOME:-$HOME/llm-wiki}/<wiki-name>/` by default; a repo may also contain one. A wiki is a folder whose `CLAUDE.md` names the `llm-wiki` skill, next to `index.md`, `raw/`, and `wiki/`. Skip this section for purely conversational answers. When a task read or changed files in a repo, or researched a topic, find wikis before finishing: `find "${LLM_WIKI_HOME:-$HOME/llm-wiki}" -mindepth 2 -maxdepth 2 -name CLAUDE.md 2>/dev/null` and, in a git repo, `git ls-files -z -- ':/*CLAUDE.md' | xargs -0r grep -l 'llm-wiki'`. Then:

- Suggest: if the task turned up something non-obvious within a wiki's scope (its `CLAUDE.md`) that its `index.md` doesn't cover, end your reply with a one-line suggestion to add it. Read `index.md` only for wikis whose scope matches. Do not write it.
- Update: if you committed a change to code that a wiki cites (`grep -rlxF -- "origin: <repo origin>" "<wiki>/raw/code" 2>/dev/null`), update that wiki without asking, following "Code change update" in the `llm-wiki` skill's `ingest.md`, and list the wiki changes in your reply. If your change is not committed, say the wiki update is pending.
