"""scanner.py 測試:既有的 _parse self-check 邏輯,加上 resolve_git_dir() 在
根目錄/子目錄/worktree 下的真實行為,以及找不到 git 執行檔時的行為。"""
from __future__ import annotations

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

from repo_chronicle import scanner  # noqa: E402


class ParseSelfCheckTest(unittest.TestCase):
    def test_self_check(self) -> None:
        scanner._self_check()  # 既有 fixture-string parse 邏輯,斷言在函式內部


class ResolveGitDirTest(unittest.TestCase):
    def test_repo_root_returns_dot_git(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            git_dir = scanner.resolve_git_dir(repo_path)
            self.assertEqual(os.path.normpath(git_dir), os.path.join(repo_path, ".git"))
            self.assertTrue(os.path.isdir(git_dir))

    def test_subdirectory_resolves_same_git_dir_as_root(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            subdir = os.path.join(repo_path, "sub")
            os.makedirs(subdir)
            root_git_dir = scanner.resolve_git_dir(repo_path)
            sub_git_dir = scanner.resolve_git_dir(subdir)
            # realpath 兩邊都做:macOS 上 tempfile 給的路徑經過 /var -> /private/var
            # symlink,git 內部對子目錄的解析會把它攤平,對根目錄呼叫則不一定會,
            # 這是系統層級的路徑正規化差異,不是我們要驗證的行為。
            self.assertEqual(os.path.realpath(root_git_dir), os.path.realpath(sub_git_dir))

    def test_worktree_resolves_its_own_git_dir_not_a_missing_directory(self) -> None:
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
                git_dir = scanner.resolve_git_dir(wt_path)
                # worktree 的 git-dir 是一個真實存在的目錄(在主 repo 的 .git/worktrees/ 底下),
                # 不是天真假設的 <wt_path>/.git(那裡其實是個檔案,不是目錄)。
                self.assertTrue(os.path.isdir(git_dir), git_dir)
                self.assertFalse(os.path.isdir(os.path.join(wt_path, ".git")))

    def test_non_git_directory_raises_git_command_error(self) -> None:
        with tempfile.TemporaryDirectory() as not_a_repo:
            with self.assertRaises(scanner.GitCommandError):
                scanner.resolve_git_dir(not_a_repo)

    def test_missing_git_executable_raises_git_not_found_error(self) -> None:
        with fixture_repo() as (repo_path, _commits):
            empty_bin = tempfile.mkdtemp(prefix="empty-path-")
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = empty_bin
            try:
                with self.assertRaises(scanner.GitNotFoundError):
                    scanner.resolve_git_dir(repo_path)
            finally:
                os.environ["PATH"] = old_path
                os.rmdir(empty_bin)


class ScanTest(unittest.TestCase):
    def test_scan_returns_real_commits_from_fixture(self) -> None:
        with fixture_repo() as (repo_path, commits):
            scanned = scanner.scan(repo_path)
            self.assertEqual(len(scanned), len(commits))
            scanned_shas = {c.hash for c in scanned}
            for c in commits:
                self.assertIn(c.sha, scanned_shas)

    def test_scan_non_git_directory_raises_git_command_error(self) -> None:
        with tempfile.TemporaryDirectory() as not_a_repo:
            with self.assertRaises(scanner.GitCommandError):
                scanner.scan(not_a_repo)


if __name__ == "__main__":
    unittest.main()
