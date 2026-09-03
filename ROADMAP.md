# Roadmap

No dates below — this is a small side project, worked on when it's worked
on. Nothing here is a promise; it's a record of what's actually being
considered versus what's deliberately staying out.

## Product boundary (fixed)

Repo Chronicle is a small, local-first CLI that turns relevant Git history
into a commit-evidenced Markdown context pack for one proposed change. It is
not becoming an MCP server, a RAG/vector-search system, a code graph, a
hosted service, or a telemetry product, and it does not require GateRail (or
anything else) to function. Anything below that would cross that line is
listed as explicitly out of scope, not as a future phase.

## Near term (plausible, not scheduled)

- **Output-language flag.** The generated Markdown's section headers are
  currently Traditional Chinese only; an `--lang en|zh-TW` (or similar) is
  the likely shape, kept as two plain string templates rather than a
  translation framework.
- **Optional output redaction/exclusion controls.** v0.1.0 reproduces commit
  subjects/bodies verbatim with no filtering (documented in
  [SECURITY.md](SECURITY.md)); an opt-in way to exclude paths or redact
  patterns before rendering is worth exploring, without turning into a
  general secret-scanning product.
- **Incremental indexing.** Every `explain` call currently rescans full
  `git log` history; storing "last indexed commit" and only reading new
  commits would help on large repositories.
- **Smarter test-file matching.** Current matching is filename-pattern-only
  and directory-agnostic (a same-named test file in an unrelated directory
  can false-positive); directory-proximity or path-similarity ranking is a
  plausible improvement, still without reading file contents.
- **A versioned output schema (frontmatter, evidence/summary/inference
  labels per line).** Deliberately *not* part of v0.1.0 — this would be a
  breaking change to the generated format and needs its own compatibility
  plan, not a drive-by addition. Tracked here as "being thought about," not
  scheduled.

## Exploration (unproven ideas, may never happen)

- A plain-Markdown handoff convention compatible with how
  [GateRail](https://github.com/richardkuo2002/gaterail-skill) structures
  its own context files — as an optional convention two independent tools
  could both read, never as a required dependency in either direction.
- More worked examples of the manual "paste the pack into a coding
  assistant session" workflow across different assistants, beyond the one
  in [`examples/walkthrough.md`](examples/walkthrough.md).
- Optional extraction of repository-level conventions (e.g. a CONTRIBUTING
  checklist, a commit-message convention) as a distinct, clearly-labeled
  section — still commit-evidenced, still not semantic analysis.

## Explicitly out of scope

- MCP server, plugin, or any native coding-assistant integration claim not
  backed by an actual tested integration.
- Vector database, embeddings, RAG, or any LLM call of any kind.
- Code graph / static analysis beyond what `git log` already reports.
- Hosted service, accounts, API keys, telemetry, analytics.
- Broad "repository intelligence" unrelated to citing history for one
  proposed change (e.g. dependency graphs, architecture diagrams).
- A required dependency on GateRail or any other specific tool.
- New external runtime dependencies without a concrete, documented reason.
