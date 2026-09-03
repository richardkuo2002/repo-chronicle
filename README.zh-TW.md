# Repo Chronicle

> Local-first 的 Git 歷史 context pack 工具:在改動一個 repo 之前,先看懂它的過去。

[English](README.md) | [繁體中文](README.zh-TW.md)

## 為什麼需要它

AI coding agent 或新加入的貢獻者能讀到 repo 目前的檔案內容,但讀不到「這段程式碼為什麼長這樣」的歷史脈絡:這個函式為什麼這樣寫?之前試過什麼、後來又改掉了?哪些檔案常常一起變動?這些答案其實都在 `git log` 裡,但原始的 `git log` 太廣、太沒結構,沒辦法直接拿給一次聚焦的修改用——結果通常是乾脆跳過歷史,或是自己一筆一筆翻 commit。

## Repo Chronicle 產出什麼

對一個關鍵字下一條指令,Repo Chronicle 就會掃描本地 commit 歷史,挑出真的提到這個關鍵字的 commit(訊息或變動檔案路徑命中皆算),寫出一份 Markdown context pack:哪些 commit 相關、改了什麼、哪些檔案常一起出現、哪些測試檔可能對應得上。每一條資訊都附著 commit hash,你可以自己拿去跟 `git show` 對照查證。

## 它不做什麼

- 不會把 repo 資料送到任何地方。全部運算都是本地的 `git log` subprocess 呼叫加上本地 SQLite 索引。Repo Chronicle 目前只呼叫本機 Git 指令,Python 原始碼中未包含網路用戶端。`tests/test_no_network.py` 會以靜態方式檢查已知的網路相關 import;它不是作業系統層級的網路隔離機制。
- 不會替你做實作決策。它只負責把歷史攤開給你(或你的 coding agent)看,決定怎麼做還是你的事。
- 不保證找到全部相關歷史——這是關鍵字比對,不是語意搜尋。
- 不含 diff 實際內容。只會告訴你哪些檔案變動、加減幾行,不會附上 diff 裡的程式碼本身。
- commit subject 與 body 會**原文重現**。如果 repo 歷史裡曾經在 commit message 留下機密,符合查詢條件時就會出現在產生的 pack 裡——分享輸出前請自己先看過。詳見 [SECURITY.md](SECURITY.md)。
- 不能取代 code review、測試,或專案自己的文件。

## 快速開始

```bash
git clone https://github.com/richardkuo2002/repo-chronicle.git
cd repo-chronicle
pip install -e .
```

先對一個一次性、決定性的 fixture repo 試試看,不用拿真的專案冒險:

```bash
python examples/create_fixture_repo.py --keep
# 印出 fixture repo 的路徑與 commit 清單,並保留在磁碟上
repo-chronicle explain report --repo <上面印出的路徑>
```

這正是那條指令的真實輸出(完整 walkthrough 與每個區塊代表的意思見
[`examples/walkthrough.md`](examples/walkthrough.md)):

```markdown
# Context Pack: report

生成時間:2026-09-04 03:31 | Repo: `/tmp/.../repo-chronicle-fixture-4vfri1jb` | 命中 commit 數:4

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

對一個真實 repo:

```bash
repo-chronicle explain auth --repo /path/to/your/repo --out pack.md
```

## 指令參考

```text
repo-chronicle explain <keyword> [--repo PATH] [--out FILE] [--top N]
```

| 參數 | 意義 | 預設值 |
|---|---|---|
| `keyword` | 用來比對 commit subject/body 與變動檔案路徑的文字關鍵字 | 必填 |
| `--repo` | 目標 repo 路徑(可以是根目錄、子目錄,或 worktree) | `.` |
| `--out` | 輸出到這個檔案,不給就印到 stdout | stdout |
| `--top` | 「可能受影響的檔案」表格最多列出幾筆 | `15` |

`--out FILE` 若目標檔案已存在會直接覆寫,不會要求確認。工具不會自動建立缺少的父目錄;`FILE` 可指定為任何可寫入的檔案路徑,不限於被分析 repository 內。

結束碼:成功(含 0 筆命中)為 `0`;預期內的操作性失敗(不是 git repo、找不到 git、`--out` 無法寫入、本地索引無法建立)一律為 `1`;CLI 語法錯誤為 `2`(argparse 內建行為)。

## 如何搭配 coding agent 使用輸出

Repo Chronicle 目前沒有跟 Claude Code、Codex、Cursor 或任何工具做過驗證過的原生整合,它只會輸出純 Markdown。預期的使用方式是:

```text
把產生的 context pack 附加或貼進你的 coding assistant session,並明確告訴它
commit 連結與引用內容是「歷史脈絡」,不是「目前的需求」。
```

Coding assistant 仍然應該去讀 repo 目前的檔案再行動——commit 描述的是「當時發生了什麼」,不一定等於「現在還是這樣」。

## 輸出格式與證據規則

Pack 依序有四個區塊:

1. **演進脈絡** — 直接證據。每一則命中 commit 一條:SHA、日期、subject、body 前幾行(引用)、以及該 commit 用 `git log --numstat` 算出的變動檔案與增刪行數。
2. **可能受影響的檔案** — 衍生的聚合結果,不是單一 commit 的證據:統計有多少命中 commit 動過每個路徑,附一個代表性 commit SHA。想知道是哪些 commit,回頭看第 1 節。
3. **建議執行的測試** — 檔名規則式猜測(`test_x.py` / `x_test.py` / `x.test.js` / `x.spec.js`),不是證據。猜不到會明確說,不會悶不吭聲。
4. **附註** — 固定的提醒:本報告是規則式產生,請以 commit hash 為準查證。

這個版本沒有替輸出加 frontmatter、schema 版本號,或逐行的 evidence/summary/inference 標籤——實際規劃與明確延後的項目見 [ROADMAP.md](ROADMAP.md)。

## 隱私與 local-only 行為

以下都是讀原始碼(`src/repo_chronicle/`)驗證過的事實,不是假設:

- 唯一會呼叫的外部程式是 `git`(`git rev-parse --git-dir`、`git log --numstat`),一律用 argv list 呼叫,不經過 shell。
- 整個套件沒有任何網路相關的 import——`tests/test_no_network.py` 用解析每個原始碼檔案 import 的方式驗證這件事。
- 本地索引檔(`repo_chronicle.sqlite3`)存在 repo 解析出來的 Git metadata 目錄底下(`git rev-parse --git-dir`),不會進 working tree——不會變成一個容易被「目標」repo 的 `git add -A` 誤 commit 進去的散落檔案。
- commit subject/body 文字會原文重現在產生的 pack 裡。這個版本(v0.1.0)不會掃描或遮蔽機密內容,詳見 [SECURITY.md](SECURITY.md)。

## 目前的限制

- 沒有語意搜尋,只有關鍵字子字串比對。
- 沒有獨立的 co-change 分析,只有「這次查詢命中的 commit 裡,這個檔案出現幾次」這種即席統計,不落表。
- 不支援多 repo、remote repo、增量索引(每次都全量重掃)。
- 測試檔猜測純靠檔名規則,不理解程式碼內容。

## 開發

本地怎麼跑測試與 fixture 產生器,見 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

MIT
