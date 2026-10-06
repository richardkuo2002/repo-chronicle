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

# 兩組純字串模板,不是翻譯框架——只覆蓋固定的區塊標題/提示文字,不覆蓋 commit
# 內容本身(那是 git 歷史的原文,不屬於「介面語言」)。
_LABELS = {
    "zh-TW": {
        "generated_at": "生成時間",
        "repo": "Repo",
        "hits": "命中 commit 數",
        "evolution_header": "## 演進脈絡(依時間排序)",
        "no_commits": "(未找到相關 commit)",
        "affected_files_label": "受影響檔案:",
        "omitted": "...(其餘 {n} 筆省略,詳見資料庫)",
        "affected_section_header": "## 可能受影響的檔案(依相關 commit 出現次數排序)",
        "table_header": "| 檔案路徑 | 出現次數 | 最近變動 commit |",
        "none": "(無)",
        "tests_section_header": "## 建議執行的測試",
        "test_line": "{test}(對應 {file})",
        "no_test_found": "⚠ {file} 未偵測到對應測試檔,建議人工確認",
        "notes_section_header": "## 附註",
        "notes_text": "本報告純規則式產生,未經語意分析,請以 commit hash 為準自行查證。",
        "query_truncated": "⚠ 符合關鍵字的 commit 數超過查詢上限({n}),以下只包含最近 {n} 筆——可能還有更舊的相關 commit 沒列出,換更精確的關鍵字查詢可縮小範圍。",
    },
    "en": {
        "generated_at": "Generated",
        "repo": "Repo",
        "hits": "Matched commits",
        "evolution_header": "## Evolution (chronological)",
        "no_commits": "(no matching commits found)",
        "affected_files_label": "Files touched:",
        "omitted": "...({n} more omitted, see local index)",
        "affected_section_header": "## Likely Affected Files (by matched-commit frequency)",
        "table_header": "| File | Occurrences | Sample commit |",
        "none": "(none)",
        "tests_section_header": "## Suggested Tests to Run",
        "test_line": "{test} (for {file})",
        "no_test_found": "⚠ no matching test file found for {file} — verify manually",
        "notes_section_header": "## Notes",
        "notes_text": "This report is rule-based, not semantic analysis. Verify against the commit hashes shown.",
        "query_truncated": "⚠ More commits matched this keyword than the query limit ({n}) — only the most recent {n} are included below. There may be older matching commits not shown; a more specific keyword narrows this.",
    },
}


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


def render(result: ExplainResult, repo_path: str, lang: str = "en") -> str:
    t = _LABELS[lang]
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Context Pack: {result.keyword}",
        "",
        f"{t['generated_at']}:{now} | {t['repo']}: {_code_span(repo_path)} | {t['hits']}:{len(result.commits)}",
        "",
    ]
    if result.truncated and result.max_commits is not None:
        lines.append(t["query_truncated"].format(n=result.max_commits))
        lines.append("")
    lines += [
        t["evolution_header"],
        "",
    ]

    if not result.commits:
        lines.append(t["no_commits"])
    for c in result.commits[:_MAX_COMMITS_SHOWN]:
        date = c.committed_at.split("T")[0]
        lines.append(f"### {date} {_code_span(c.hash[:10])} — {_escape_backticks(c.subject)}")
        if c.body:
            body_preview = "\n".join(_escape_backticks(l) for l in c.body.splitlines()[:3])
            lines.append(f"> {body_preview}")
        if c.files:
            lines.append("")
            lines.append(t["affected_files_label"])
            for f in c.files:
                add = f["additions"] if f["additions"] is not None else "?"
                dele = f["deletions"] if f["deletions"] is not None else "?"
                lines.append(f"- {_code_span(f['path'])} (+{add}/-{dele})")
        lines.append("")
    if len(result.commits) > _MAX_COMMITS_SHOWN:
        lines.append(t["omitted"].format(n=len(result.commits) - _MAX_COMMITS_SHOWN))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(t["affected_section_header"])
    lines.append("")
    if result.affected_files:
        lines.append(t["table_header"])
        lines.append("|---|---|---|")
        for f in result.affected_files:
            lines.append(
                f"| {_table_cell(f.path)} | {f.occurrences} | {_table_cell(f.sample_hash[:10])} |"
            )
    else:
        lines.append(t["none"])
    lines.append("")

    lines.append(t["tests_section_header"])
    lines.append("")
    for f in result.affected_files:
        if f.test_candidates:
            for c_ in f.test_candidates:
                lines.append(f"- {t['test_line'].format(test=_code_span(c_), file=_code_span(f.path))}")
        else:
            lines.append(f"- {t['no_test_found'].format(file=_code_span(f.path))}")
    if not result.affected_files:
        lines.append(t["none"])
    lines.append("")

    lines.append(t["notes_section_header"])
    lines.append("")
    lines.append(t["notes_text"])
    lines.append("")

    return "\n".join(lines)
