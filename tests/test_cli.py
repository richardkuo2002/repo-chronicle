"""CLI 端對端測試:用 examples/create_fixture_repo.py 建的決定性 fixture repo,
斷言真實產生的 SHA/順序/範圍,不用寫死在文件裡的假值。"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_EXAMPLES_DIR = str(Path(__file__).resolve().parent.parent / "examples")
if _EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, _EXAMPLES_DIR)

from create_fixture_repo import fixture_repo  # noqa: E402

from repo_chronicle import cli  # noqa: E402


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    """呼叫 cli.main(),回傳 (exit_code, stdout, stderr)。argparse 語法錯誤會
    直接 sys.exit(2),這裡一併接住轉成一致的回傳形狀給測試用。"""
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    return code, out.getvalue(), err.getvalue()


class ExplainAgainstFixtureTest(unittest.TestCase):
    """證據可追溯性 + 順序穩定性 + 範圍正確性,用真實 fixture repo 驗證。"""

    def test_matched_commit_evidence_is_traceable_and_ordered_newest_first(self) -> None:
        with fixture_repo() as (repo_path, commits):
            code, out, err = _run_cli(["explain", "report", "--repo", repo_path])
            self.assertEqual(code, 0, err)

            # fixture 全部 4 個 commit 的 subject 都含 "report" 相關內容(檔名/訊息),
            # 直接用 build() 回傳的真實 subject/SHA 反查,而不是寫死期望值。
            newest_first = list(reversed(commits))
            for commit in newest_first:
                self.assertIn(commit.sha[:10], out, "SHA 必須原樣出現在輸出裡才可追溯")
                self.assertIn(commit.subject, out)

            # 順序穩定:SHA 出現的先後順序要跟「由新到舊」一致。
            positions = [out.index(c.sha[:10]) for c in newest_first]
            self.assertEqual(positions, sorted(positions), "commit 必須依時間新到舊排序")

    def test_query_scope_excludes_unrelated_commits(self) -> None:
        with fixture_repo() as (repo_path, commits):
            # "portability" 只出現在其中一個 commit subject 裡。
            code, out, _ = _run_cli(["explain", "portability", "--repo", repo_path])
            self.assertEqual(code, 0)
            matched = [c for c in commits if "portability" in c.subject]
            unmatched = [c for c in commits if "portability" not in c.subject]
            self.assertEqual(len(matched), 1)
            for c in matched:
                self.assertIn(c.sha[:10], out)
            for c in unmatched:
                self.assertNotIn(c.sha[:10], out, "不相關的 commit 不該混進結果")

    def test_output_is_deterministic_ignoring_timestamp_line(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            _, out1, _ = _run_cli(["explain", "report", "--repo", repo_path])
            _, out2, _ = _run_cli(["explain", "report", "--repo", repo_path])

            def strip_timestamp(text: str) -> str:
                return "\n".join(
                    line for line in text.splitlines() if not line.startswith("生成時間:")
                )

            self.assertEqual(strip_timestamp(out1), strip_timestamp(out2))


class GitDirDetectionTest(unittest.TestCase):
    """.git 偵測要在 repo 根目錄、子目錄、worktree 下都正確運作。"""

    def test_repo_root(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            code, _out, err = _run_cli(["explain", "report", "--repo", repo_path])
            self.assertEqual(code, 0, err)

    def test_subdirectory_of_repo(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            subdir = os.path.join(repo_path, "sub")
            os.makedirs(subdir)
            code, _out, err = _run_cli(["explain", "report", "--repo", subdir])
            self.assertEqual(code, 0, err)

    def test_git_worktree(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            with tempfile.TemporaryDirectory() as wt_parent:
                wt_path = os.path.join(wt_parent, "wt")
                subprocess.run(
                    ["git", "worktree", "add", "-q", wt_path],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertTrue(os.path.isfile(os.path.join(wt_path, ".git")))  # 前提:worktree 的 .git 是檔案
                code, _out, err = _run_cli(["explain", "report", "--repo", wt_path])
                self.assertEqual(code, 0, err)

    def test_non_git_directory_gives_clean_error_not_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as not_a_repo:
            code, _out, err = _run_cli(["explain", "x", "--repo", not_a_repo])
            self.assertEqual(code, 1)
            self.assertIn("git repository", err)
            self.assertNotIn("Traceback", err)


class MissingGitExecutableTest(unittest.TestCase):
    def test_missing_git_gives_clean_error_not_traceback(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            empty_bin = tempfile.mkdtemp(prefix="empty-path-")
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = empty_bin
            try:
                code, _out, err = _run_cli(["explain", "x", "--repo", repo_path])
            finally:
                os.environ["PATH"] = old_path
                os.rmdir(empty_bin)
            self.assertEqual(code, 1)
            self.assertIn("git", err)
            self.assertNotIn("Traceback", err)


class OutWriteFailureTest(unittest.TestCase):
    def test_out_path_that_is_a_directory_gives_clean_error(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            with tempfile.TemporaryDirectory() as out_dir:
                code, _out, err = _run_cli(
                    ["explain", "report", "--repo", repo_path, "--out", out_dir]
                )
                self.assertEqual(code, 1)
                self.assertNotIn("Traceback", err)


class InvalidCliInputTest(unittest.TestCase):
    def test_missing_required_keyword_exits_with_argparse_code(self) -> None:
        code, _out, err = _run_cli(["explain"])
        self.assertEqual(code, 2)  # argparse 既有結束碼,不能改
        self.assertNotIn("Traceback", err)


class IndexLocationTest(unittest.TestCase):
    def test_index_is_written_under_git_dir_not_worktree_root(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            code, _out, err = _run_cli(["explain", "report", "--repo", repo_path])
            self.assertEqual(code, 0, err)

            git_dir_index = os.path.join(repo_path, ".git", "repo_chronicle.sqlite3")
            root_index = os.path.join(repo_path, "repo_chronicle.sqlite3")
            self.assertTrue(os.path.isfile(git_dir_index), "索引檔應該在 .git/ 底下")
            self.assertFalse(os.path.isfile(root_index), "repo 根目錄不該出現索引檔")


if __name__ == "__main__":
    unittest.main()
