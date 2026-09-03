"""規則式篩選/排序邏輯。吃 db 查詢結果,吐結構化資料,不做任何語意分析。"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field

from . import db as db_mod

_TEST_PATTERNS = [
    "test_{name}{ext}",
    "{name}_test{ext}",
    "{name}.test{ext}",
    "{name}.spec{ext}",
]


@dataclass
class CommitEntry:
    hash: str
    author: str
    committed_at: str
    subject: str
    body: str
    files: list  # list of sqlite3.Row(path, additions, deletions)


@dataclass
class AffectedFile:
    path: str
    occurrences: int
    sample_hash: str
    test_candidates: list[str] = field(default_factory=list)


@dataclass
class ExplainResult:
    keyword: str
    commits: list[CommitEntry]
    affected_files: list[AffectedFile]


def _guess_test_candidates(path: str, known_paths: list[str]) -> list[str]:
    """對 path 猜測對應測試檔:basename 字串規則比對曾出現過的路徑。"""
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    if not ext:
        return []
    wanted_basenames = {p.format(name=name, ext=ext) for p in _TEST_PATTERNS}
    candidates = [
        p for p in known_paths
        if os.path.basename(p) in wanted_basenames and p != path
    ]
    return sorted(set(candidates))


def explain(conn: sqlite3.Connection, keyword: str, top_n: int = 15) -> ExplainResult:
    hit_rows = db_mod.search_commits(conn, keyword)
    commits = [
        CommitEntry(
            hash=r["hash"],
            author=r["author"],
            committed_at=r["committed_at"],
            subject=r["subject"],
            body=r["body"],
            files=db_mod.files_for_commit(conn, r["hash"]),
        )
        for r in hit_rows
    ]

    hashes = [c.hash for c in commits]
    file_rows = db_mod.files_for_commits(conn, hashes, top_n=top_n)
    known_paths = db_mod.all_known_paths(conn)
    affected = [
        AffectedFile(
            path=r["path"],
            occurrences=r["occurrences"],
            sample_hash=r["sample_hash"],
            test_candidates=_guess_test_candidates(r["path"], known_paths),
        )
        for r in file_rows
    ]

    return ExplainResult(keyword=keyword, commits=commits, affected_files=affected)


def _self_check() -> None:
    conn = db_mod.connect(":memory:")
    db_mod.init_schema(conn)

    from dataclasses import dataclass as _dc

    @_dc
    class F:
        path: str
        additions: int | None
        deletions: int | None

    @_dc
    class C:
        hash: str
        author: str
        email: str
        committed_at: str
        subject: str
        body: str
        files: list

    commits_in = [
        C("h1", "Alice", "a@x.com", "2024-01-02T00:00:00+08:00", "Fix auth token", "",
          [F("src/auth/token.py", 3, 1)]),
        C("h2", "Bob", "b@x.com", "2024-01-01T00:00:00+08:00", "Add token tests", "",
          [F("tests/auth/test_token.py", 20, 0), F("src/auth/token.py", 1, 0)]),
        C("h3", "Carl", "c@x.com", "2023-12-01T00:00:00+08:00", "Unrelated readme change", "",
          [F("README.md", 5, 0)]),
    ]
    db_mod.index_repo(conn, commits_in)

    result = explain(conn, "auth", top_n=10)
    assert [c.hash for c in result.commits] == ["h1", "h2"], result.commits
    assert result.affected_files[0].path == "src/auth/token.py"
    assert result.affected_files[0].occurrences == 2

    token_entry = next(f for f in result.affected_files if f.path == "src/auth/token.py")
    assert token_entry.test_candidates == ["tests/auth/test_token.py"], token_entry.test_candidates

    readme_entry_missing = all(f.path != "README.md" for f in result.affected_files)
    assert readme_entry_missing  # 不相關的 commit 不該混進來

    conn.close()
    print("explain._self_check: OK")


if __name__ == "__main__":
    _self_check()
