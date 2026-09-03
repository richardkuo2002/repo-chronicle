"""結構化資料轉 Markdown 字串。不做任何篩選邏輯,純字串組裝。

Git 資料(commit subject/body、檔案路徑)可能含 Markdown 特殊字元(反引號、
`|`、換行),原封不動塞進 Markdown 會弄壞表格欄位或不小心開啟一段沒有結尾的
code span,吃掉後面整份文件的格式。以下三個 helper 只負責「讓字元組合本身不
破壞 Markdown 結構」,不做內容過濾/摘要/遮蔽 —— 一般 commit 內容(不含這些
特殊字元時)的輸出與跳脫前逐位元組相同。
"""
from __future__ import annotations

import datetime as _dt

from .explain import ExplainResult

_MAX_COMMITS_SHOWN = 20  # 避免關鍵字太常見時整份報告爆長,超過的部分只算在統計裡


def _escape_backticks(text: str) -> str:
    """在純文字位置(標題、引言)跳脫反引號,避免奇數個反引號意外開啟一段沒有
    結尾的 code span,吃掉後面整份文件的格式。一般文字(無反引號)原樣不變。"""
    return text.replace("`", "\\`")


def _code_span(text: str) -> str:
    """把 text 包成安全的 inline code span:定界符長度取「內容中最長連續反引號
    數 + 1」,內容以反引號開頭/結尾時前後加空白(CommonMark 規則),避免內容
    本身的反引號提前結束 code span。內容不含反引號時,結果與原本的 `` `text` ``
    寫法逐位元組相同。"""
    text = text.replace("\n", " ")
    longest_run = 0
    current = 0
    for ch in text:
        if ch == "`":
            current += 1
            longest_run = max(longest_run, current)
        else:
            current = 0
    fence = "`" * (longest_run + 1)
    if text == "" or text.startswith("`") or text.endswith("`"):
        return f"{fence} {text} {fence}"
    return f"{fence}{text}{fence}"


def _table_cell(text: str) -> str:
    """把 text 放進 Markdown 表格欄位。表格欄位以未跳脫的 `|` 分欄,而不同
    Markdown 渲染器對「表格分欄」與「code span」的解析順序並不一致,不能保證
    code span 一定能保護裡面的 `|`(CommonMark 的反斜線跳脫本身在 code span
    內也不生效)。因此含 `|` 的內容改成跳脫成一般文字,不包 code span —— 這是
    唯一在各種渲染器下都安全的作法。不含 `|` 時走 `_code_span`,逐位元組相容。"""
    text = text.replace("\n", " ")
    if "|" in text:
        return text.replace("\\", "\\\\").replace("|", "\\|").replace("`", "\\`")
    return _code_span(text)


def render(result: ExplainResult, repo_path: str) -> str:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Context Pack: {result.keyword}",
        "",
        f"生成時間:{now} | Repo: {_code_span(repo_path)} | 命中 commit 數:{len(result.commits)}",
        "",
        "## 演進脈絡(依時間排序)",
        "",
    ]

    if not result.commits:
        lines.append("(未找到相關 commit)")
    for c in result.commits[:_MAX_COMMITS_SHOWN]:
        date = c.committed_at.split("T")[0]
        lines.append(f"### {date} {_code_span(c.hash[:10])} — {_escape_backticks(c.subject)}")
        if c.body:
            body_preview = "\n".join(_escape_backticks(l) for l in c.body.splitlines()[:3])
            lines.append(f"> {body_preview}")
        if c.files:
            lines.append("")
            lines.append("受影響檔案:")
            for f in c.files:
                add = f["additions"] if f["additions"] is not None else "?"
                dele = f["deletions"] if f["deletions"] is not None else "?"
                lines.append(f"- {_code_span(f['path'])} (+{add}/-{dele})")
        lines.append("")
    if len(result.commits) > _MAX_COMMITS_SHOWN:
        lines.append(f"...(其餘 {len(result.commits) - _MAX_COMMITS_SHOWN} 筆省略,詳見資料庫)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 可能受影響的檔案(依相關 commit 出現次數排序)")
    lines.append("")
    if result.affected_files:
        lines.append("| 檔案路徑 | 出現次數 | 最近變動 commit |")
        lines.append("|---|---|---|")
        for f in result.affected_files:
            lines.append(
                f"| {_table_cell(f.path)} | {f.occurrences} | {_table_cell(f.sample_hash[:10])} |"
            )
    else:
        lines.append("(無)")
    lines.append("")

    lines.append("## 建議執行的測試")
    lines.append("")
    for f in result.affected_files:
        if f.test_candidates:
            for t in f.test_candidates:
                lines.append(f"- {_code_span(t)}(對應 {_code_span(f.path)})")
        else:
            lines.append(f"- ⚠ {_code_span(f.path)} 未偵測到對應測試檔,建議人工確認")
    if not result.affected_files:
        lines.append("(無)")
    lines.append("")

    lines.append("## 附註")
    lines.append("")
    lines.append("本報告純規則式產生,未經語意分析,請以 commit hash 為準自行查證。")
    lines.append("")

    return "\n".join(lines)
