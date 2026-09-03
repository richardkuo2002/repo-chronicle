# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).
Nothing has been tagged/released yet — everything so far is `Unreleased`.

## Unreleased

### Added

- `explain <keyword>` command: scans local `git log` history, indexes it into
  a local SQLite database, and writes a Markdown context pack of matching
  commits, an affected-files aggregation, and heuristic test-file
  suggestions.
- `examples/create_fixture_repo.py`: deterministic fixture-repository
  generator (fixed author/committer/timestamps) used by tests and by
  [`examples/walkthrough.md`](examples/walkthrough.md).
- `tests/`: `unittest`-based test suite covering commit-evidence
  traceability and ordering, `.git` resolution (root/subdirectory/worktree),
  missing-`git`/non-repo/invalid-CLI-input failure handling, Markdown
  escaping of adversarial commit data, and a static no-network-imports check.
- `CONTRIBUTING.md`, `SECURITY.md`, `ROADMAP.md`, GitHub issue forms, and a
  pull request template.
- Minimal CI (`.github/workflows/ci.yml`): runs the test suite and a CLI
  `--help` smoke test.

### Fixed

- `--repo` pointing at a git **worktree** or at a **subdirectory** of a repo
  (rather than its root) was incorrectly rejected as "not a git repository".
  Detection now asks `git rev-parse --git-dir` instead of assuming `.git` is
  a directory at the given path.
- A missing `git` executable, a failed `git` subprocess, or a failed
  `--out`/local-index write previously surfaced as a raw Python traceback.
  These now print one concise message to stderr and exit `1`.
- Commit subjects/bodies or file paths containing `` ` `` or `|` could
  corrupt the generated Markdown (break table columns, or open an
  unterminated code span that swallowed the rest of the document). Both are
  now escaped/rendered safely; output for content without those characters
  is unchanged.
- SQLite connections were never closed, leaking file handles
  (`ResourceWarning: unclosed database` under test).

### Changed

- The local index (`repo_chronicle.sqlite3`) now lives under the
  repository's resolved Git metadata directory (`git rev-parse --git-dir`)
  instead of the working-tree root. This avoids leaving a
  full-commit-history SQLite file (author emails, full commit bodies)
  sitting untracked in the *target* repository's working tree, one
  `git add -A` away from being committed by mistake.
