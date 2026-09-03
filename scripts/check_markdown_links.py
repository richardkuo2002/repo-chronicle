#!/usr/bin/env python3
"""檢查專案裡所有 Markdown 檔案的「本地相對連結」是否都指到真實存在的檔案。

只管 `[text](relative/path.md#anchor)` 這種相對路徑連結,跳過 http(s)/mailto
等外部連結(那些不是這個檢查的責任,而且在沒有網路的 CI 步驟裡本來就不該去
戳外部網址)。純 stdlib,不需要額外套件。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")


def _iter_markdown_files(root: Path):
    for path in root.rglob("*.md"):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        yield path


def check(root: Path) -> list[str]:
    problems: list[str] = []
    for md_file in _iter_markdown_files(root):
        text = md_file.read_text(encoding="utf-8")
        for match in _LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(_SKIP_PREFIXES):
                continue
            target_path = target.split("#", 1)[0]  # 去掉錨點,只驗證檔案本身
            if not target_path:
                continue
            resolved = (md_file.parent / target_path).resolve()
            if not resolved.exists():
                problems.append(f"{md_file}: broken link -> {target}")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    problems = check(root)
    if problems:
        print("Broken local Markdown links found:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("All local Markdown links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
