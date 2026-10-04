# Ingest

Turn one source into wiki pages. Do the steps in order. Step 2 ends your turn.

## 0. Locate or create the wiki

Find `<wiki-root>` (see SKILL.md) and read its `CLAUDE.md`.

If there is no wiki, ask the user whether to create one in the current directory. If yes:

1. Ask for a one-sentence scope (or propose one and get it confirmed).
2. Create `raw/web/`, `raw/pdf/`, `raw/code/`, `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`. Put an empty `.gitkeep` file in each so the layout survives a git clone (`find_root` needs `raw/` and `wiki/`).
3. Copy `templates/CLAUDE.md`, `templates/index.md`, and `templates/log.md` into the wiki root. Fill in the topic and scope in `CLAUDE.md`. Append `## [YYYY-MM-DD] create | <topic>` to `log.md`.
4. Do not run `git init`. If `git -C <wiki-root> rev-parse --is-inside-work-tree` prints `true`, commit only the wiki:
   `git -C <wiki-root> add -- . && git -C <wiki-root> commit -m "Create wiki for <topic>" -- .`

## 1. Capture the source into raw/

Pick a slug (see Naming in SKILL.md). The slug must be unused: if `raw/*/<slug>.*` or `wiki/sources/<slug>.md` already exists, either it is the same source (a duplicate, see below) or you add a letter suffix (`dao-2022b`). Never overwrite or replace a file under `raw/`.

Check for a duplicate first: `grep -rlF -- "origin: <origin>" <wiki-root>/raw <wiki-root>/wiki/sources`. If one exists, tell the user which file and ask whether to skip or re-ingest. Re-ingesting code at a newer commit creates a new manifest and source page (new slug), and the check-in plans updates to the pages that cite the old one.

Raw files go in exactly one of `raw/web/`, `raw/pdf/`, `raw/code/`, by kind. Do not create any other folder under `raw/`.

**Web** (`raw/web/`)
1. Get the full text: `curl -fsSL "<url>" -o "<scratchpad>/page.html"`, then convert with the first tool that exists: `pandoc -f html -t gfm page.html`, `markdownify page.html`, `html2text page.html`.
2. Write `raw/web/<slug>.md` with frontmatter `origin: <url>` and `fetched: <YYYY-MM-DD>`, then the converted text.
3. If curl fails or no converter exists, use WebFetch and ask it for the full article text verbatim. Add `capture: lossy` to the raw file and later to the source page, and tell the user the capture is lossy.

**PDF** (`raw/pdf/`)
1. Copy the file to `raw/pdf/<slug>.pdf`, or download it there with `curl -fsSL "<url>" -o "<wiki-root>/raw/pdf/<slug>.pdf"`.
2. Read it with the Read tool's `pages` parameter, at most 20 pages per call. Note the page number of everything you will cite. Section and Table numbers are not a substitute for `p.<n>`.

**Code** (`raw/code/`)
1. Use a local path as-is, or `git clone --depth 1 -- "<url>" "<scratchpad>/<repo>"`.
   - A local path that is not a git repo cannot be pinned to a commit (lint requires a 40-character `commit:`). Tell the user and ask whether to proceed; do not invent a SHA.
   - A local git repo with uncommitted changes: tell the user the manifest's commit will not match what was read, and ask whether to proceed.
2. Record the full SHA (`git -C <repo> rev-parse HEAD`) and the origin: `git -C <repo> remote get-url origin` if it exists, else the absolute local path.
3. Read what matters for this wiki's scope and the user's focus: README, layout, the relevant modules. Do not try to read everything.
4. Write `raw/code/<repo>-<shortsha>.md` (7-character SHA from `git -C <repo> rev-parse --short=7 HEAD`) with frontmatter `origin`, `commit`, `read: <YYYY-MM-DD>`, and a body listing every path you actually read. List paths only; do not copy code into the manifest.

## 2. Check in, then end your turn

Before writing this source's changes to `wiki/`, `index.md`, or `log.md` (creating a new wiki in step 0 is separate and already approved), send the user:

- **Takeaways:** 3–5 main points, with page numbers for PDFs.
- **Planned changes:** one line each, e.g. `create wiki/concepts/kv-cache.md`, `update wiki/entities/tinyattn.md (+ section on batching)`.
- **Conflicts:** every place the source disagrees with an existing page, quoting both sides with citations. Write "none" if there are none.

End your turn and wait for approval. Apply any corrections the user gives before writing. Files captured into `raw/` in step 1 may already exist; they are inputs, not wiki changes.

### Red flags — you are about to skip the check-in

Derived from baseline behavior: agents ingested three different sources without pausing even once, treating "add X to the wiki" as a full mandate.

- You are about to create or edit a page under `wiki/` and the user has not replied to your takeaways.
- You plan to "report the conflict in the summary" after writing.
- You have not sent takeaways, planned changes, and conflicts in a message that ended your turn.

**All of these mean: stop writing, send the check-in, end your turn.**

| Thought | Reality |
|---|---|
| "The user asked me to add it, so that's approval" | The request authorizes capturing the source. Approval of specific page changes comes only after you show them. |
| "The user is in a hurry" | The check-in is one short message. Writing first and fixing later costs more of their time. |
| "I'll report the conflict at the end" | A conflict reported after writing is already baked into the pages. Surface it before. |
| "The change is small and obviously right" | You cannot know that until the user has seen the planned changes. |

## 3. Write the pages

1. Create the source page `wiki/sources/<slug>.md` from `templates/source.md`. For code sources add `commit: <full SHA>`; for WebFetch captures add `capture: lossy` (both are commented out in the template).
2. Create or update each planned entity and concept page (templates: `entity.md`, `concept.md`). Every new claim cites the source page.
3. For each conflict, leave the existing claim in place and add directly below it this exact single line:
   `> **Conflict:** [a](../sources/a.md) says X; [b, p.N](../sources/b.md) says Y. Unresolved.`
   Do not pick a winner or add a separate section.
4. On every touched entity or concept page, add the source page to `sources:` and set `updated:` to today.
5. Make sure every new page is linked from at least one other wiki page, usually the source page's "Touches" list.

## 4. Bookkeeping

Add or update the `index.md` line for every created or changed page. Append `## [YYYY-MM-DD] ingest | <source title>` to `log.md`.

## 5. Lint

Run `python3 <this skill's base directory>/scripts/lint.py <wiki-root>` and fix every finding this ingest introduced until only unrelated ones remain (exit 0 if none). Report pre-existing unrelated findings to the user instead of fixing them, and never edit files under `raw/` to silence `raw-modified`.

## 6. Commit

If `git -C <wiki-root> rev-parse --is-inside-work-tree` prints `true`, the commit is part of the ingest. It is not optional and not left for the user:
`git -C <wiki-root> add -- . && git -C <wiki-root> commit -m "Ingest <source title>" -- .`
This commits only the wiki's own paths. Otherwise skip committing; `log.md` is the record.

Finish by listing the files created and updated.
