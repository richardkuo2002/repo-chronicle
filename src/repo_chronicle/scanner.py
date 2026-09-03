"""掃 git log,parse 成結構化 commit 資料。只管「怎麼從 git 拿到 commit 資料」,不碰 SQLite。"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field

# 用不會出現在一般 commit 內容裡的控制字元當分隔符,避免 message 裡有 tab/逗號時 parsing 出錯。
_START = "\x02"  # 一筆 commit 的起始
_FIELD = "\x1f"  # 欄位分隔
_END = "\x03"  # commit 中繼資料結束,後面接 numstat 行


class GitNotFoundError(Exception):
    """系統上找不到 git 執行檔。訊息刻意精簡,不附帶路徑或原始指令。"""


class GitCommandError(Exception):
    """git 指令執行失敗(例如目標路徑不是 git repo)。訊息刻意精簡,不附帶路徑或原始指令。"""


@dataclass
class FileChange:
    path: str
    additions: int | None
    deletions: int | None


@dataclass
class Commit:
    hash: str
    author: str
    email: str
    committed_at: str  # ISO8601
    subject: str
    body: str
    files: list[FileChange] = field(default_factory=list)


def _run_git(args: list[str], repo_path: str) -> subprocess.CompletedProcess:
    """跑一條 git 指令,只把「找不到 git 執行檔」轉成明確例外;成功與否(returncode)
    交給呼叫者自己判斷,呼叫者才知道怎麼描述失敗才對使用者有意義。
    """
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitNotFoundError("git executable not found") from exc
    except NotADirectoryError as exc:
        raise GitCommandError("repo path is not a valid directory") from exc


def resolve_git_dir(repo_path: str) -> str:
    """回傳 git metadata 目錄(.git)的絕對路徑,用 `git rev-parse --git-dir` 取得,
    而不是假設 `.git` 一定是目錄——worktree 底下 `.git` 是指向真正 gitdir 的檔案,
    子目錄底下則根本沒有 `.git`,兩種情況 git 自己都能正確解析,不用我們猜。
    """
    result = _run_git(["rev-parse", "--git-dir"], repo_path)
    if result.returncode != 0:
        raise GitCommandError("repo path is not a valid git repository")
    git_dir = result.stdout.strip()
    if not os.path.isabs(git_dir):
        git_dir = os.path.normpath(os.path.join(os.path.abspath(repo_path), git_dir))
    else:
        git_dir = os.path.normpath(git_dir)
    return git_dir


def scan(repo_path: str) -> list[Commit]:
    """跑 git log,回傳該 repo 全部 commit(含檔案異動)。

    repo_path 可以是 repo 根目錄、子目錄,或 git worktree ——不預先檢查 `.git`
    是否存在,讓 git 自己判斷,失敗時轉成明確例外(GitNotFoundError/GitCommandError)。
    """
    fmt = f"{_START}%H{_FIELD}%an{_FIELD}%ae{_FIELD}%aI{_FIELD}%s{_FIELD}%b{_END}"
    result = _run_git(["log", "--numstat", f"--pretty=format:{fmt}"], repo_path)
    if result.returncode != 0:
        raise GitCommandError("git log failed for this repo path")
    return _parse(result.stdout)


def _parse(output: str) -> list[Commit]:
    commits: list[Commit] = []
    # 第一個 chunk 是 _START 之前的空字串,丟掉
    for chunk in output.split(_START)[1:]:
        meta_part, _, rest = chunk.partition(_END)
        fields = meta_part.split(_FIELD)
        if len(fields) != 6:
            continue  # 格式不符,跳過(不該發生,防禦性處理)
        chash, author, email, date, subject, body = fields
        commit = Commit(
            hash=chash,
            author=author,
            email=email,
            committed_at=date,
            subject=subject,
            body=body.strip(),
        )
        for line in rest.strip("\n").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            add_s, del_s, path = parts
            additions = int(add_s) if add_s.isdigit() else None
            deletions = int(del_s) if del_s.isdigit() else None
            commit.files.append(FileChange(path=path, additions=additions, deletions=deletions))
        commits.append(commit)
    return commits


def _self_check() -> None:
    fixture = (
        f"{_START}abc123{_FIELD}Alice{_FIELD}alice@example.com{_FIELD}"
        f"2024-01-02T03:04:05+08:00{_FIELD}Fix token bug{_FIELD}"
        f"Body line 1\nBody line 2{_END}"
        "\n3\t1\tsrc/auth/token.py\n0\t5\tsrc/auth/old.py\n\n"
        f"{_START}def456{_FIELD}Bob{_FIELD}bob@example.com{_FIELD}"
        f"2024-01-01T00:00:00+08:00{_FIELD}Initial commit{_FIELD}{_END}\n"
        "10\t0\tREADME.md\n"
    )
    commits = _parse(fixture)
    assert len(commits) == 2, f"expected 2 commits, got {len(commits)}"

    first = commits[0]
    assert first.hash == "abc123"
    assert first.author == "Alice"
    assert first.subject == "Fix token bug"
    assert first.body == "Body line 1\nBody line 2"
    assert len(first.files) == 2, first.files
    assert first.files[0] == FileChange("src/auth/token.py", 3, 1)
    assert first.files[1] == FileChange("src/auth/old.py", 0, 5)

    second = commits[1]
    assert second.hash == "def456"
    assert second.body == ""
    assert len(second.files) == 1
    assert second.files[0] == FileChange("README.md", 10, 0)

    print("scanner._self_check: OK")


if __name__ == "__main__":
    _self_check()
