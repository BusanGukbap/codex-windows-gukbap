#!/usr/bin/env bash
# Create a small git repo whose code is documented by an llm-wiki inside it.
# Usage: seed-code-repo.sh DIR [WIKI_DIR]
#   DIR is deleted and recreated. WIKI_DIR defaults to DIR/docs/wiki; if it is
#   outside DIR it is deleted and recreated and left uncommitted (no git).
set -euo pipefail

dir=$1
rm -rf "$dir"
mkdir -p "$dir/calc"
dir=$(cd "$dir" && pwd)
git_() { git -C "$dir" -c user.name=Test -c user.email=test@example.com -c commit.gpgsign=false "$@"; }

cat > "$dir/calc/__init__.py" <<'EOF'
EOF
cat > "$dir/calc/ops.py" <<'EOF'
def add(a, b):
    return a + b


def div(a, b):
    if b == 0:
        return float("inf")
    return a / b
EOF
git_ init -q
git_ add -A
git_ commit -q -m "Add calc ops"
sha=$(git_ rev-parse HEAD)
short=$(git_ rev-parse --short=7 HEAD)
today=$(date +%F)

w=${2:-$dir/docs/wiki}
case "$w" in "$dir"/*) ;; *) rm -rf "$w" ;; esac
mkdir -p "$w/raw/web" "$w/raw/pdf" "$w/raw/code" "$w/wiki/sources" "$w/wiki/entities" "$w/wiki/concepts"

cat > "$w/CLAUDE.md" <<'EOF'
# Wiki: calc

This directory is an LLM wiki maintained with the `llm-wiki` skill. Use that skill for any ingest, query, or lint here.

## Scope

Behavior and API of the `calc` package in this repository.

## Page types

Core: `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`. Extra: none.

## Naming

Kebab-case slugs. Sources: `<author>-<year>` or `<site>-<title-words>`; code: `<repo>-<shortsha>`.
EOF

cat > "$w/index.md" <<EOF
# Index

## Sources

- [calc @ $short](wiki/sources/calc-$short.md) — the calc package source

## Entities

- [calc](wiki/entities/calc.md) — small arithmetic package

## Concepts

- [Addition](wiki/concepts/addition.md) — how calc adds numbers
EOF

cat > "$w/log.md" <<EOF
# Log

## [$today] ingest | calc @ $short
EOF

cat > "$w/raw/code/calc-$short.md" <<EOF
---
origin: $dir
commit: $sha
read: $today
---
# calc @ $short

Paths read:

- calc/ops.py (add only)
EOF

cat > "$w/wiki/sources/calc-$short.md" <<EOF
---
title: calc @ $short
type: source
sources: []
raw: raw/code/calc-$short.md
origin: $dir
commit: $sha
updated: $today
---
# calc @ $short

Raw: [calc-$short](../../raw/code/calc-$short.md)

## Summary

The calc package exposes arithmetic helpers in \`calc/ops.py\`.

## Key claims

- \`calc.ops.add(a, b)\` returns \`a + b\`.

## Touches

- [calc](../entities/calc.md) — what the package is
- [Addition](../concepts/addition.md) — the add function
EOF

cat > "$w/wiki/entities/calc.md" <<EOF
---
title: calc
type: entity
sources: [wiki/sources/calc-$short.md]
updated: $today
---
# calc

Small arithmetic package in this repository ([calc-$short](../sources/calc-$short.md)). See [Addition](../concepts/addition.md).
EOF

cat > "$w/wiki/concepts/addition.md" <<EOF
---
title: Addition
type: concept
sources: [wiki/sources/calc-$short.md]
updated: $today
---
# Addition

\`calc.ops.add(a, b)\` returns the sum of its two arguments ([calc-$short](../sources/calc-$short.md)). It is the package's only documented operation; see [calc](../entities/calc.md).
EOF

w=$(cd "$w" && pwd)
case "$w" in
  "$dir"/*) git_ add -A; git_ commit -q -m "Add calc wiki" ;;
esac
echo "$dir"
