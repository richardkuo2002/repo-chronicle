"""建立一個決定性(deterministic)的 fixture git repo,供測試與 walkthrough 使用。

不在專案裡放靜態 fixture 目錄、不 commit `.git/`、不寫死 SHA 值 —— 每次呼叫才
在一個臨時目錄裡真的跑 git 指令建立,SHA 由 git 當場產生,呼叫端讀真實回傳值,
用完自動清掉。作者/committer 名稱、email、commit 時間全部固定,讓輸出(除了
SHA 本身,這是 git 內容定址的本質)在不同機器上可重現。

Fixture 的 commit 歷史刻意做成一個小而真實的「歷史決策」序列,給
docs/tests 用同一組真資料:
  1. 加入純文字報表指令
  2. 決策:stdout 給自動化消費,診斷訊息要走 stderr
  3. 決策:不加第三方執行期依賴,保持可攜性
  4. 後續功能請求:加 --json 輸出,同時保留預設文字輸出與 exit code 行為
"""
from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

_AUTHOR_NAME = "Fixture Author"
_AUTHOR_EMAIL = "fixture@example.invalid"

_REPORT_V1 = '''"""Print a plain text status report."""


def build_report(items):
    return "\\n".join(f"- {name}: {status}" for name, status in items)


def main():
    items = [("build", "ok"), ("tests", "ok")]
    print(build_report(items))


if __name__ == "__main__":
    main()
'''

_REPORT_V2 = '''"""Print a plain text status report.

Historical decision: stdout is parsed by downstream automation, so only the
report itself goes there. Diagnostics must go to stderr instead, or they
corrupt automated parsing of stdout.
"""
import sys


def build_report(items):
    return "\\n".join(f"- {name}: {status}" for name, status in items)


def main():
    items = [("build", "ok"), ("tests", "ok")]
    if not items:
        print("warning: no items to report", file=sys.stderr)
    print(build_report(items))


if __name__ == "__main__":
    main()
'''

_REPORT_V3 = '''"""Print a plain text status report.

Historical decisions:
- stdout is parsed by downstream automation; diagnostics go to stderr only.
- No third-party runtime dependency: this stays pure stdlib so it runs on any
  minimal Python install without a package-manager step.
"""
import sys


def build_report(items):
    return "\\n".join(f"- {name}: {status}" for name, status in items)


def main():
    items = [("build", "ok"), ("tests", "ok"), ("lint", "ok")]
    if not items:
        print("warning: no items to report", file=sys.stderr)
    print(build_report(items))


if __name__ == "__main__":
    main()
'''

_REPORT_V4 = '''"""Print a plain text status report, or JSON with --json.

Historical decisions:
- stdout is parsed by downstream automation; diagnostics go to stderr only.
- No third-party runtime dependency: this stays pure stdlib.
- --json was added on request without changing the default text output or
  the process exit-code contract (0 if every item is ok, 1 otherwise).
"""
import argparse
import json
import sys


def build_report(items):
    return "\\n".join(f"- {name}: {status}" for name, status in items)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    items = [("build", "ok"), ("tests", "ok"), ("lint", "ok")]
    if not items:
        print("warning: no items to report", file=sys.stderr)

    if args.json:
        print(json.dumps([{"name": n, "status": s} for n, s in items]))
    else:
        print(build_report(items))

    return 0 if all(status == "ok" for _, status in items) else 1


if __name__ == "__main__":
    sys.exit(main())
'''

_STEPS = [
    ("2024-01-01T09:00:00+00:00", "Add text report command", _REPORT_V1),
    ("2024-02-01T09:00:00+00:00", "Send diagnostics to stderr, keep stdout automation-safe", _REPORT_V2),
    ("2024-03-01T09:00:00+00:00", "Avoid third-party runtime dependency for portability", _REPORT_V3),
    ("2024-04-01T09:00:00+00:00", "Add --json output, preserve default text output and exit codes", _REPORT_V4),
]


@dataclass
class FixtureCommit:
    sha: str
    subject: str


def _git(args: list[str], cwd: str, when: str) -> None:
    env = dict(os.environ)
    env.update(
        GIT_AUTHOR_NAME=_AUTHOR_NAME,
        GIT_AUTHOR_EMAIL=_AUTHOR_EMAIL,
        GIT_COMMITTER_NAME=_AUTHOR_NAME,
        GIT_COMMITTER_EMAIL=_AUTHOR_EMAIL,
        GIT_AUTHOR_DATE=when,
        GIT_COMMITTER_DATE=when,
    )
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True)


def build(dest_dir: str) -> list[FixtureCommit]:
    """在 dest_dir(必須已存在且為空目錄)建立 fixture repo,回傳依時間順序
    排列、附真實 SHA 的 commit 清單。呼叫端自己負責建立/清除 dest_dir。"""
    first_when = _STEPS[0][0]
    _git(["init", "-q"], dest_dir, first_when)
    _git(["config", "user.name", _AUTHOR_NAME], dest_dir, first_when)
    _git(["config", "user.email", _AUTHOR_EMAIL], dest_dir, first_when)

    report_path = os.path.join(dest_dir, "report.py")
    for when, subject, content in _STEPS:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        _git(["add", "-A"], dest_dir, when)
        _git(["commit", "-q", "-m", subject], dest_dir, when)

    log = subprocess.run(
        ["git", "log", "--reverse", "--pretty=format:%H\x1f%s"],
        cwd=dest_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    for line in log.stdout.splitlines():
        sha, _, subject = line.partition("\x1f")
        commits.append(FixtureCommit(sha=sha, subject=subject))
    return commits


@contextlib.contextmanager
def fixture_repo():
    """Context manager:在一個臨時目錄建立 fixture repo,yield (repo_path,
    commits),離開 with 區塊時自動刪除臨時目錄 —— 測試與 walkthrough 都用這個
    入口,不會在檔案系統留下垃圾。"""
    tmp = tempfile.mkdtemp(prefix="repo-chronicle-fixture-")
    try:
        commits = build(tmp)
        yield tmp, commits
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _main() -> int:
    keep = "--keep" in sys.argv[1:]
    tmp = tempfile.mkdtemp(prefix="repo-chronicle-fixture-")
    commits = build(tmp)
    print(f"Fixture repo created at: {tmp}")
    for c in commits:
        print(f"  {c.sha[:10]}  {c.subject}")
    print()
    print(f"Try it:\n  repo-chronicle explain stdout --repo {tmp}")
    if keep:
        print("\n--keep given: not deleting. Remove it yourself when done:")
        print(f"  rm -rf {tmp}")
        return 0
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n(fixture repo removed — pass --keep to inspect it manually)")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
