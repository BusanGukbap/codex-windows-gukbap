---
title: Self-attention
type: concept
sources: [wiki/sources/blog-transformer-notes.md, wiki/sources/tinyattn-1a2b3c4.md]
updated: 2026-10-02
---
# Self-attention

Each token attends to every token in the same sequence.

The base Transformer uses 6 attention heads per layer ([blog-transformer-notes](../sources/blog-transformer-notes.md)).

A minimal single-head implementation exists in [tinyattn](../entities/tinyattn.md).
