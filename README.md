# Repo Chronicle

Local-first Git 歷史索引工具。掃描任意 repo 的 commit 歷史存進本地 SQLite，輸出有
commit 證據可追溯的 Markdown context pack，供 AI coding agent（Claude Code /
Codex / Cursor）在修改舊專案前快速理解某功能的演進脈絡、過去的取捨、可能受影響的
檔案與應執行的測試——不必靠模型猜測或重讀整個 codebase。

純規則式產生（無 LLM、無 embedding、無網路呼叫），資料全存在你自己的機器上。

## 安裝

```bash
git clone https://github.com/richardkuo2002/repo-chronicle.git
cd repo-chronicle
pip install -e .
```

## 使用

```bash
repo-chronicle explain <keyword> [--repo PATH] [--out FILE] [--top N]
```

- `<keyword>`：功能名稱或檔案路徑片段（會同時比對 commit message 與檔案路徑）
- `--repo`：目標 git repo 路徑，預設當前目錄
- `--out`：輸出檔案，預設印到 stdout
- `--top`：受影響檔案列出的數量上限，預設 15

每次執行會在目標 repo 下建立/重建 `.repo_chronicle.sqlite3` 索引檔（已加進
`.gitignore`，不會被誤 commit）。

## 輸出範例

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

## 目前的限制（v1，刻意先不做）

- 不做語意分析或摘要，「修改原因」就是 commit message 原文
- 不做跨 commit 的共同變更（co-change）獨立分析，只在單次查詢時即席統計
- 不支援多 repo、remote repo、增量索引（每次全量重建）
- 測試檔猜測純靠檔名規則（`test_x.py` / `x_test.py` / `x.test.js` / `x.spec.js`），
  猜不到就明確標註「建議人工確認」，不會假裝很準

歡迎 issue / PR。

## License

MIT
