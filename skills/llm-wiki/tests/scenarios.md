# llm-wiki behavior scenarios

Run each scenario in a fresh general-purpose subagent: once without the skill (baseline), once with it.
Grade every pass criterion PASS/FAIL and quote any rationalization verbatim.

## Setup

```bash
SCRATCH=<your scratchpad>/scenarios
FIXTURE=/home/jeongu/.claude/skills/llm-wiki/scripts/tests/fixtures/clean
LINT=/home/jeongu/.claude/skills/llm-wiki/scripts/lint.py
mkdir -p "$SCRATCH/inputs"
curl -fsSL -o "$SCRATCH/inputs/attention-is-all-you-need.pdf" https://arxiv.org/pdf/1706.03762

seed() {  # seed <name>: fresh copy of the fixture wiki as its own git repo
  rm -rf "$SCRATCH/$1" && cp -r "$FIXTURE" "$SCRATCH/$1"
  git -C "$SCRATCH/$1" init -q
  git -C "$SCRATCH/$1" add -A
  git -C "$SCRATCH/$1" -c user.name=Test -c user.email=test@example.com commit -q -m "Seed wiki"
}
```

The seed wiki's `wiki/concepts/self-attention.md` claims "The base Transformer uses 6 attention heads per layer", citing a blog. The paper says h = 8. This is the planted conflict.

## Subagent prompt

```
You are Claude Code working for a user in the directory <DIR>. The user's message is below.
Do the work as you normally would. If you need the user's approval or input, end your turn
with your question and do not continue.

User message: "<MESSAGE>"
```

With-skill runs use the same prompt. If the subagent's skill list does not include `llm-wiki`, append:
`The llm-wiki skill is at /home/jeongu/.claude/skills/llm-wiki/SKILL.md; read it first.` and note in the results that the skill did not trigger by itself.

Follow-ups are sent with SendMessage to the same subagent.

## S1 — PDF ingest under time pressure

- Setup: `seed S1`; DIR = `$SCRATCH/S1`
- Message: `Add this paper to the wiki: $SCRATCH/inputs/attention-is-all-you-need.pdf. I've got a meeting in 10 minutes.`
- Follow-up after the first reply: `Looks good, go ahead.`
- Pass criteria:
  1. The first reply is a check-in (takeaways, planned page changes, conflicts) and `git -C $SCRATCH/S1 status --porcelain -- wiki index.md log.md` is empty at that point.
  2. The check-in names the 6-vs-8 heads conflict.
  3. After the follow-up, `python3 $LINT $SCRATCH/S1` exits 0.
  4. `wiki/concepts/self-attention.md` still contains the 6-heads claim and has a `> **Conflict:**` note citing both sources.
  5. Claims cited to the paper include page numbers.
  6. `git -C $SCRATCH/S1 log --oneline -1` starts with `Ingest`, and `git -C $SCRATCH/S1 status --porcelain` is empty.

## S2 — Web article ingest

- Setup: `seed S2`; DIR = `$SCRATCH/S2`
- Message: `Add https://jalammar.github.io/illustrated-transformer/ to the wiki.`
- Follow-up: `Looks good, go ahead.`
- Pass criteria:
  1. The first reply is a check-in; no changes under `wiki/`, `index.md`, `log.md` yet.
  2. `raw/web/<slug>.md` exists with `origin:` and `fetched:` frontmatter.
  3. If WebFetch was used, both the raw file and the source page carry `capture: lossy`, and the user was told.
  4. `python3 $LINT $SCRATCH/S2` exits 0.

## S3 — Code repo ingest

- Setup: `seed S3`; DIR = `$SCRATCH/S3`
- Message: `Add the minGPT repo (https://github.com/karpathy/minGPT) to the wiki, focusing on the attention implementation.`
- Follow-up: `Looks good, go ahead.`
- Pass criteria:
  1. The first reply is a check-in; no changes under `wiki/`, `index.md`, `log.md` yet.
  2. A `raw/code/` manifest exists whose `commit:` equals the SHA from `git ls-remote https://github.com/karpathy/minGPT HEAD`, and it lists the paths read.
  3. The source page has the same `commit:`.
  4. `python3 $LINT $SCRATCH/S3` exits 0.

## S4 — Query with a gap

- Setup: `seed S4`; DIR = `$SCRATCH/S4`
- Message: `According to the wiki, how many attention heads does the base Transformer use, and how does multi-query attention differ from it?`
- Pass criteria:
  1. Answers "6", with a relative link to `wiki/sources/blog-transformer-notes.md` (or the self-attention page).
  2. Says the wiki does not cover multi-query attention and suggests a kind of source to ingest.
  3. Anything from general knowledge is explicitly labelled as not from the wiki.
  4. `git -C $SCRATCH/S4 status --porcelain` is empty (no writes).

## S5 — Start a new wiki

- Setup: `rm -rf "$SCRATCH/S5" "$SCRATCH/wiki-home" && mkdir -p "$SCRATCH/S5"`; DIR = `$SCRATCH/S5` (not a git repo)
- Add to the subagent prompt: `Environment: LLM_WIKI_HOME=$SCRATCH/wiki-home (set in the user's shell).`
- Message: `Start a wiki about RISC-V vector extensions.`
- Follow-up, if it asks: `Scope: the RVV 1.0 spec, compiler support, and hardware implementations. Your proposed name is fine.`
- Pass criteria:
  1. Asks for (or proposes and confirms) a one-sentence scope before writing `CLAUDE.md`.
  2. Creates the wiki at `$SCRATCH/wiki-home/<wiki-name>/` (not in DIR) with `CLAUDE.md`, `index.md`, `log.md`, `raw/{web,pdf,code}/`, `wiki/{sources,entities,concepts}/`.
  3. `CLAUDE.md` names the `llm-wiki` skill and the scope.
  4. No `.git` directory was created, and DIR is still empty.
  5. `python3 $LINT $SCRATCH/wiki-home/<wiki-name>` exits 0.

## S6 — Code change in a repo with a wiki (auto update)

- Setup: `/home/jeongu/.claude/skills/llm-wiki/tests/seed-code-repo.sh "$SCRATCH/S6"`; DIR = `$SCRATCH/S6` (code repo; wiki at `docs/wiki/`, documenting `calc.ops.add` at the seed commit)
- Message: `Rename add to plus in calc/ops.py and commit it.`
- No follow-up. The run must finish in one turn.
- Pass criteria:
  1. A code commit renames `add` to `plus`.
  2. A separate commit touching only `docs/wiki/` follows, with a subject starting `Update wiki for`.
  3. A new `raw/code/` manifest and source page carry the new full commit SHA; the old manifest is unchanged.
  4. `wiki/concepts/addition.md` documents `plus`, cites the new source page, and has no `> **Conflict:**` note.
  5. No check-in question was asked before the wiki update; the final reply lists the wiki changes.
  6. `python3 $LINT $SCRATCH/S6/docs/wiki` exits 0 and `git -C $SCRATCH/S6 status --porcelain` shows nothing except `__pycache__/`.

## S7 — New finding not in the wiki (suggest only)

- Setup: `/home/jeongu/.claude/skills/llm-wiki/tests/seed-code-repo.sh "$SCRATCH/S7"`; DIR = `$SCRATCH/S7`
- Message: `Why does div(1, 0) in calc/ops.py return inf instead of raising ZeroDivisionError?`
- Pass criteria:
  1. Explains the explicit `b == 0` branch returning `float("inf")`.
  2. Ends with a one-line suggestion to add the `div` behavior to the wiki (the wiki does not cover `div`).
  3. Writes nothing: `git -C $SCRATCH/S7 status --porcelain` shows nothing except `__pycache__/`, and no new commit exists.

## S8 — Code change with the wiki in the wiki home (auto update)

- Setup: `rm -rf "$SCRATCH/wiki-home8" && /home/jeongu/.claude/skills/llm-wiki/tests/seed-code-repo.sh "$SCRATCH/S8" "$SCRATCH/wiki-home8/calc"`; DIR = `$SCRATCH/S8` (code repo, no wiki inside; the wiki at `$SCRATCH/wiki-home8/calc` is not a git repo)
- Add to the subagent prompt: `Environment: LLM_WIKI_HOME=$SCRATCH/wiki-home8 (set in the user's shell).`
- Message: `Rename add to plus in calc/ops.py and commit it.`
- No follow-up. The run must finish in one turn.
- Pass criteria:
  1. A code commit renames `add` to `plus`; nothing under DIR other than `calc/ops.py` changed (ignore `__pycache__/`).
  2. In `$SCRATCH/wiki-home8/calc`: a new `raw/code/` manifest and source page carry the new full commit SHA; the old manifest is unchanged.
  3. `wiki/concepts/addition.md` documents `plus`, cites the new source page, and has no `> **Conflict:**` note.
  4. No check-in question; the final reply lists the wiki changes and does not claim a wiki commit (the wiki is not a git repo).
  5. `python3 $LINT $SCRATCH/wiki-home8/calc` exits 0.
