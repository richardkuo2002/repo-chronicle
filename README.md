# Repo Chronicle

[English](README.md) | [繁體中文](README.zh-TW.md)

A local-first Git history indexer. It scans any repo's commit history into a
local SQLite database and produces a commit-evidenced Markdown context pack
for AI coding agents (Claude Code / Codex / Cursor) — so you can understand
how a feature evolved, what trade-offs were made, which files are likely
affected, and which tests to run, before touching legacy code, without
guessing or re-reading the whole codebase.

Rule-based only (no LLM, no embeddings, no network calls). All data stays on
your machine.

## Install

```bash
git clone https://github.com/richardkuo2002/repo-chronicle.git
cd repo-chronicle
pip install -e .
```

## Usage

```bash
repo-chronicle explain <keyword> [--repo PATH] [--out FILE] [--top N]
```

- `<keyword>`: a feature name or file path fragment (matched against both
  commit messages and file paths)
- `--repo`: target git repo path, defaults to the current directory
- `--out`: output file, defaults to stdout
- `--top`: max number of affected files listed, defaults to 15

Each run builds/rebuilds a `.repo_chronicle.sqlite3` index inside the target
repo (already in `.gitignore`, safe from accidental commits).

## Example output

The tool currently renders Markdown section headers in Traditional Chinese
(see the [Chinese README](README.zh-TW.md) for the real, unedited output).
Below is an English translation for readability:

```markdown
# Context Pack: auth

Generated: 2024-11-03 10:00 | Repo: `/path/to/project` | Matched commits: 2

## Evolution (newest first)

### 2024-11-02 `a1b2c3d1e2` — Refactor auth token refresh logic
> Fixed the refresh token expiry check using <= instead of <, causing tokens
> to expire one second early...

Affected files:
- `src/auth/token.py` (+42/-11)
- `src/auth/middleware.py` (+8/-2)

---

## Likely affected files (by occurrence count across matched commits)

| File | Occurrences | Most recent commit |
|---|---|---|
| `src/auth/token.py` | 6 | `a1b2c3d1e2` |

## Suggested tests to run

- `tests/auth/test_token.py` (for `src/auth/token.py`)
- ⚠ no matching test file found for `src/auth/session.py` — please confirm manually

## Notes

This report is rule-based, not semantic analysis — verify against the commit
hashes yourself.
```

An `--lang en` flag to make the actual render output English is a possible
future improvement — not implemented yet.

## Current limits (v1, intentionally deferred)

- No semantic analysis or summarization — "why it changed" is the raw commit
  message.
- No standalone co-change table — related files are computed on the fly per
  query, not pre-aggregated.
- No multi-repo, no remote repos, no incremental indexing (full rescan every
  run).
- Test-file guessing is filename-pattern only (`test_x.py` / `x_test.py` /
  `x.test.js` / `x.spec.js`); when it can't guess, it says so explicitly
  instead of pretending to be accurate.

Issues and PRs welcome.

## License

MIT
