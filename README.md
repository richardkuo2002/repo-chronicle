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

The generated Markdown itself is currently in Traditional Chinese (section
headers included) — this is the real, unedited output:

```markdown
# Context Pack: auth

生成時間:2024-11-03 10:00 | Repo: `/path/to/project` | 命中 commit 數:2

## 演進脈絡(依時間排序)

### 2024-11-02 `a1b2c3d1e2` — Refactor auth token refresh logic
> 修正 refresh token 過期判斷用了 <= 導致提早一秒失效...

受影響檔案:
- `src/auth/token.py` (+42/-11)
- `src/auth/middleware.py` (+8/-2)

---

## 可能受影響的檔案(依相關 commit 出現次數排序)

| 檔案路徑 | 出現次數 | 最近變動 commit |
|---|---|---|
| `src/auth/token.py` | 6 | `a1b2c3d1e2` |

## 建議執行的測試

- `tests/auth/test_token.py`(對應 `src/auth/token.py`)
- ⚠ `src/auth/session.py` 未偵測到對應測試檔,建議人工確認

## 附註

本報告純規則式產生,未經語意分析,請以 commit hash 為準自行查證。
```

Localizing the render output itself (e.g. an `--lang en` flag) is a possible
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
