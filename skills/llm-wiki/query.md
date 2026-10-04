# Query

Answer from the wiki. A query is read-only: write no files and make no commits.

1. Find `<wiki-root>` (see SKILL.md). If there is none, say so and stop.
2. Read `index.md` first. Choose candidate pages from their one-line summaries.
3. Read those pages. Follow their links one or two levels only where the answer needs it.
4. Open files in `raw/` only to verify a specific detail, such as an exact number or a quote.
5. Answer with citations as markdown links with paths relative to the wiki root, e.g. `([dao-2022, p.4](wiki/sources/dao-2022.md))`. Bare paths in backticks are not citations.
6. If the wiki does not cover part of the question, say which part and suggest a kind of source to ingest. If you add anything from general knowledge, label it explicitly as not from the wiki.
7. If you notice an unresolved `> **Conflict:**` or a page that looks stale, mention it in one line. Do not fix it; that is the lint operation's job.
8. Do not offer to save the answer to the wiki; answers stay in chat.
