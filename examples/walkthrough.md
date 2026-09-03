# Walkthrough: generating and using a context pack

This walkthrough uses the deterministic fixture repository built by
[`create_fixture_repo.py`](create_fixture_repo.py). Everything below —
commit SHAs, dates, and the generated Markdown — was captured from an actual
run against that fixture, not written by hand.

## 1. Create the fixture repo

```bash
python examples/create_fixture_repo.py --keep
```

This builds a small git repository (fixed author, fixed commit timestamps)
with four commits that tell a real, small history:

1. `Add text report command`
2. `Send diagnostics to stderr, keep stdout automation-safe`
3. `Avoid third-party runtime dependency for portability`
4. `Add --json output, preserve default text output and exit codes`

The script prints the repo's path and its real commit SHAs, then leaves the
directory in place (because of `--keep`) so you can point `repo-chronicle`
at it. Without `--keep` the directory is created, used, and removed
automatically — that's what the test suite does.

## 2. Generate a context pack

```bash
repo-chronicle explain report --repo <fixture path printed above>
```

Real output from this exact command:

```markdown
# Context Pack: report

生成時間:2026-09-04 03:26 | Repo: `/tmp/.../repo-chronicle-fixture-o848n1bo` | 命中 commit 數:4

## 演進脈絡(依時間排序)

### 2024-04-01 `e4900b7e08` — Add --json output, preserve default text output and exit codes

受影響檔案:
- `report.py` (+18/-5)

### 2024-03-01 `1521a1e2da` — Avoid third-party runtime dependency for portability

受影響檔案:
- `report.py` (+5/-4)

### 2024-02-01 `787d4bcf11` — Send diagnostics to stderr, keep stdout automation-safe

受影響檔案:
- `report.py` (+9/-1)

### 2024-01-01 `7510ef4bd1` — Add text report command

受影響檔案:
- `report.py` (+14/-0)

---

## 可能受影響的檔案(依相關 commit 出現次數排序)

| 檔案路徑 | 出現次數 | 最近變動 commit |
|---|---|---|
| `report.py` | 4 | `e4900b7e08` |

## 建議執行的測試

- ⚠ `report.py` 未偵測到對應測試檔,建議人工確認

## 附註

本報告純規則式產生,未經語意分析,請以 commit hash 為準自行查證。
```

(The repo path above is specific to the run that produced this walkthrough —
yours will differ, since it's a fresh temp directory each time. The **commit
SHAs will match**, though: author, committer, commit dates, and file content
are all fixed by the generator, and a git commit's hash is a function of
exactly those inputs plus its parent — so the same fixture build produces the
same SHAs on any machine. `tests/test_fixture_repo.py` asserts this.)

## 3. What each part of the output actually is

The sections aren't labeled "evidence" / "summary" / "inference" in the
generated file itself (that labeling scheme is deferred, not part of this
release) — but here's what each section is, concretely, as of this version:

- **`## 演進脈絡` (evolution) section** — direct evidence. Each entry is one
  real commit: its SHA, date, subject, and (when present) the first lines of
  its body, quoted, plus the exact files it touched with add/delete counts
  from `git log --numstat`. Nothing here is generated text — verify any of it
  yourself with `git show <sha>`.
- **`## 可能受影響的檔案` (affected files) table** — a derived aggregation,
  not a single commit's evidence. It counts how many matched commits touched
  each path and lists the most recent matching commit as a reference. If
  `report.py` shows "4" here, that means 4 of the matched commits touched it
  — read the evolution section above to see which ones and why, don't take
  the count as a ranking of importance.
- **`## 建議執行的測試` (suggested tests) section** — a heuristic guess, not
  evidence. It matches filename patterns (`test_x.py`, `x_test.py`,
  `x.test.js`, `x.spec.js`) against paths that appeared in this repo's
  history. It found no match for `report.py` in this fixture (there is no
  `report.test.py` in it) — the ⚠ line saying so is the tool being honest
  about a gap, not a claim that no tests exist.

## 4. Handing this to a coding assistant

Repo Chronicle does not have a tested native integration with any specific
coding assistant. What it produces is plain Markdown. The intended workflow
is manual:

1. Run `repo-chronicle explain <keyword> --repo <your repo> --out pack.md`
   (or just copy the stdout output).
2. Paste or attach `pack.md` into your coding-assistant session (Claude Code,
   Codex, Cursor, or anything else that reads Markdown).
3. Tell the assistant explicitly that the commit references are **historical
   context**, not current requirements — code may have changed since a
   quoted commit, and the assistant should still read the current files
   before acting on what the pack says.
4. Treat the affected-files table and test suggestions as a starting point
   to verify, not a guarantee — the tool itself says as much in its
   `## 附註` footer.

## 5. One honest limitation to carry into that conversation

Commit subjects and bodies are reproduced **verbatim** in the generated
Markdown. If a real repository's history ever contains a secret in a commit
message, running `explain` with a matching keyword will surface it in the
output file. Review a generated pack before pasting it into a shared
session or an external tool. See [`SECURITY.md`](../SECURITY.md).
