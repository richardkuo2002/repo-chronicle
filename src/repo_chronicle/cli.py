"""argparse entrypoint。串接 scanner/db/explain/render,不含業務邏輯。"""
from __future__ import annotations

import argparse
import contextlib
import os
import sqlite3
import sys

from . import db as db_mod
from . import scanner
from .explain import explain
from .render import render

_DB_FILENAME = "repo_chronicle.sqlite3"  # 存在 git metadata 目錄底下,不進 working tree
_OPERATIONAL_ERROR_EXIT = 1  # 所有「使用者/環境」層級的失敗共用同一個 exit code


def _cmd_explain(args: argparse.Namespace) -> int:
    repo_path = os.path.abspath(args.repo)

    try:
        git_dir = scanner.resolve_git_dir(repo_path)
    except scanner.GitNotFoundError:
        print("錯誤:找不到 git 執行檔,請確認已安裝並加入 PATH", file=sys.stderr)
        return _OPERATIONAL_ERROR_EXIT
    except scanner.GitCommandError:
        print(f"錯誤:{args.repo} 不是有效的 git repository", file=sys.stderr)
        return _OPERATIONAL_ERROR_EXIT

    db_path = os.path.join(git_dir, _DB_FILENAME)
    try:
        conn = db_mod.connect(db_path)
    except sqlite3.Error:
        print("錯誤:無法建立或開啟本地索引資料庫", file=sys.stderr)
        return _OPERATIONAL_ERROR_EXIT

    with contextlib.closing(conn):
        try:
            db_mod.init_schema(conn)
        except sqlite3.Error:
            print("錯誤:無法建立或開啟本地索引資料庫", file=sys.stderr)
            return _OPERATIONAL_ERROR_EXIT

        try:
            commits = scanner.scan(repo_path)
        except scanner.GitNotFoundError:
            print("錯誤:找不到 git 執行檔,請確認已安裝並加入 PATH", file=sys.stderr)
            return _OPERATIONAL_ERROR_EXIT
        except scanner.GitCommandError:
            print(f"錯誤:{args.repo} 不是有效的 git repository", file=sys.stderr)
            return _OPERATIONAL_ERROR_EXIT

        db_mod.index_repo(conn, commits)

        result = explain(conn, args.keyword, top_n=args.top)
        output = render(result, repo_path)

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(output)
        except OSError:
            print(f"錯誤:無法寫入輸出檔案 {args.out}", file=sys.stderr)
            return _OPERATIONAL_ERROR_EXIT
        print(f"已寫入 {args.out}")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-chronicle")
    sub = parser.add_subparsers(dest="command", required=True)

    p_explain = sub.add_parser("explain", help="輸出某功能/檔案關鍵字的 context pack")
    p_explain.add_argument("keyword", help="要查詢的文字關鍵字(比對 commit message 與檔案路徑)")
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
