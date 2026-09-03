"""examples/create_fixture_repo.py 本身的契約測試:確保其他測試與 walkthrough
依賴的假設(commit 數、順序、清理行為)是對的。"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_EXAMPLES_DIR = str(Path(__file__).resolve().parent.parent / "examples")
if _EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, _EXAMPLES_DIR)

from create_fixture_repo import fixture_repo  # noqa: E402


class FixtureRepoTest(unittest.TestCase):
    def test_builds_four_commits_in_chronological_order(self) -> None:
        with fixture_repo() as (repo_path, commits):
            self.assertTrue(os.path.isdir(os.path.join(repo_path, ".git")))
            self.assertEqual(len(commits), 4)
            subjects = [c.subject for c in commits]
            self.assertEqual(
                subjects,
                [
                    "Add text report command",
                    "Send diagnostics to stderr, keep stdout automation-safe",
                    "Avoid third-party runtime dependency for portability",
                    "Add --json output, preserve default text output and exit codes",
                ],
            )
            # 每筆都要有一個看起來像真的 git SHA 的值(40 個十六進位字元),不是佔位字串。
            for c in commits:
                self.assertEqual(len(c.sha), 40)
                self.assertTrue(all(ch in "0123456789abcdef" for ch in c.sha))

    def test_directory_is_removed_after_context_manager_exits(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            captured_path = repo_path
        self.assertFalse(os.path.exists(captured_path))

    def test_shas_are_reproducible_across_separate_builds(self) -> None:
        # 作者/committer/commit 時間/內容全部固定,git 的 commit hash 是這些輸入
        # (加上 parent)的函數,所以兩次獨立建立的 fixture repo 應該產生完全一樣
        # 的 SHA —— 這是 walkthrough.md 裡引用固定 SHA 值的前提,這裡鎖住它。
        with fixture_repo() as (_repo_path_a, commits_a):
            shas_a = [c.sha for c in commits_a]
        with fixture_repo() as (_repo_path_b, commits_b):
            shas_b = [c.sha for c in commits_b]
        self.assertEqual(shas_a, shas_b)


if __name__ == "__main__":
    unittest.main()
