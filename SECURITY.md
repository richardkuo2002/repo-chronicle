# Security Policy

## Reporting a vulnerability

Please don't open a public issue for a security vulnerability, and don't
post exploit details publicly before a fix is available. Instead, reach the
maintainer through the contact method(s) listed on their GitHub profile
([github.com/richardkuo2002](https://github.com/richardkuo2002)) — GitHub's
private vulnerability reporting on this repository, if enabled, is also
fine. Include what you'd include in a normal bug report (see the issue
template) plus enough detail to reproduce the issue.

## What's actually in scope

Repo Chronicle currently invokes only local Git commands and does not
include a network client in its Python source. `tests/test_no_network.py`
statically checks for known networking imports; it is not an
operating-system network sandbox. It also has **zero third-party runtime
dependencies**, and its only external process call is `git`, always invoked
as an argv list, never through a shell. Given that
shape, in-scope reports look like: a way to make it execute something other
than the intended `git` command, a path-handling bug that reads/writes
outside the intended repository or index location, or a way to corrupt its
generated Markdown into something that misrepresents the underlying commit
evidence.

## What's a known, accepted behavior — not a vulnerability report

- **Generated context packs can contain sensitive historical content.**
  Commit subjects and bodies are reproduced verbatim, unredacted. If a
  repository's history ever had a secret in a commit message, a matching
  `explain` query will surface it in the output file. This tool does not
  scan for or redact secrets in v0.1.0 (see [ROADMAP.md](ROADMAP.md)) —
  **review a generated pack before sharing it externally or pasting it into
  another tool.**
- The local SQLite index (stored under the repository's resolved Git
  metadata directory, not the working tree — see the README) contains the
  same commit history data as the pack: author name/email, full commit
  bodies, and per-file change stats. It never leaves the machine it was
  built on, but it is not encrypted.
