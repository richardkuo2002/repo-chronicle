# Repo Chronicle

Local-first Git 歷史索引工具。掃描任意 repo 的 commit 歷史存進本地 SQLite，
輸出有 commit 證據可追溯的 Markdown context pack，供 AI coding agent
（Claude Code / Codex / Cursor）在修改舊專案前快速理解某功能的演進脈絡。

## 安裝

```bash
pip install -e .
```

## 使用

```bash
repo-chronicle explain <keyword> [--repo PATH] [--out FILE] [--top N]
```

- `--repo`：目標 git repo 路徑，預設當前目錄
- `--out`：輸出檔案，預設印到 stdout
- `--top`：受影響檔案列出的數量上限，預設 15

輸出純規則式產生（無 LLM），每條資訊皆附 commit hash 供人工查證。
