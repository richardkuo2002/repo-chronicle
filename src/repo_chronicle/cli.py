"""argparse entrypoint。串接 scanner/db/explain/render,不含業務邏輯。"""
from __future__ import annotations

import argparse
import os
import sys

from . import db as db_mod
from . import scanner
from .explain import explain
from .render import render

_DB_FILENAME = ".repo_chronicle.sqlite3"


def _cmd_explain(args: argparse.Namespace) -> int:
    repo_path = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"錯誤:{repo_path} 不是一個 git repo(找不到 .git)", file=sys.stderr)
        return 1

    db_path = os.path.join(repo_path, _DB_FILENAME)
    conn = db_mod.connect(db_path)
    db_mod.init_schema(conn)

    commits = scanner.scan(repo_path)
    db_mod.index_repo(conn, commits)

    result = explain(conn, args.keyword, top_n=args.top)
    output = render(result, repo_path)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"已寫入 {args.out}")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-chronicle")
    sub = parser.add_subparsers(dest="command", required=True)

    p_explain = sub.add_parser("explain", help="輸出某功能/檔案關鍵字的 context pack")
    p_explain.add_argument("keyword", help="要查詢的關鍵字(功能名稱或檔案路徑片段)")
    p_explain.add_argument("--repo", default=".", help="目標 git repo 路徑(預設當前目錄)")
    p_explain.add_argument("--out", default=None, help="輸出檔案路徑(預設印到 stdout)")
    p_explain.add_argument("--top", type=int, default=15, help="受影響檔案列出的數量上限(預設 15)")
    p_explain.set_defaults(func=_cmd_explain)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
