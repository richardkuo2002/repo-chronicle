"""結構化資料轉 Markdown 字串。不做任何篩選邏輯,純字串組裝。"""
from __future__ import annotations

import datetime as _dt

from .explain import ExplainResult

_MAX_COMMITS_SHOWN = 20  # 避免關鍵字太常見時整份報告爆長,超過的部分只算在統計裡


def render(result: ExplainResult, repo_path: str) -> str:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Context Pack: {result.keyword}",
        "",
        f"生成時間:{now} | Repo: `{repo_path}` | 命中 commit 數:{len(result.commits)}",
        "",
        "## 演進脈絡(依時間排序)",
        "",
    ]

    if not result.commits:
        lines.append("(未找到相關 commit)")
    for c in result.commits[:_MAX_COMMITS_SHOWN]:
        date = c.committed_at.split("T")[0]
        lines.append(f"### {date} `{c.hash[:10]}` — {c.subject}")
        if c.body:
            body_preview = "\n".join(c.body.splitlines()[:3])
            lines.append(f"> {body_preview}")
        if c.files:
            lines.append("")
            lines.append("受影響檔案:")
            for f in c.files:
                add = f["additions"] if f["additions"] is not None else "?"
                dele = f["deletions"] if f["deletions"] is not None else "?"
                lines.append(f"- `{f['path']}` (+{add}/-{dele})")
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
            lines.append(f"| `{f.path}` | {f.occurrences} | `{f.sample_hash[:10]}` |")
    else:
        lines.append("(無)")
    lines.append("")

    lines.append("## 建議執行的測試")
    lines.append("")
    for f in result.affected_files:
        if f.test_candidates:
            for t in f.test_candidates:
                lines.append(f"- `{t}`(對應 `{f.path}`)")
        else:
            lines.append(f"- ⚠ `{f.path}` 未偵測到對應測試檔,建議人工確認")
    if not result.affected_files:
        lines.append("(無)")
    lines.append("")

    lines.append("## 附註")
    lines.append("")
    lines.append("本報告純規則式產生,未經語意分析,請以 commit hash 為準自行查證。")
    lines.append("")

    return "\n".join(lines)
