"""SQLite 建表/寫入/查詢。只管「怎麼存/查 SQLite」,不懂 git、不懂 Markdown。"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

_SCHEMA = """
CREATE TABLE IF NOT EXISTS commits (
    hash         TEXT PRIMARY KEY,
    author       TEXT NOT NULL,
    email        TEXT,
    committed_at TEXT NOT NULL,
    subject      TEXT NOT NULL,
    body         TEXT
);

CREATE TABLE IF NOT EXISTS commit_files (
    hash       TEXT NOT NULL REFERENCES commits(hash),
    path       TEXT NOT NULL,
    status     TEXT,
    additions  INTEGER,
    deletions  INTEGER,
    PRIMARY KEY (hash, path)
);

CREATE INDEX IF NOT EXISTS idx_commit_files_path ON commit_files(path);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def index_repo(conn: sqlite3.Connection, commits) -> None:
    """把 scanner.scan() 回傳的 commit 清單寫進 db(全量重建:先清空再寫)。"""
    conn.execute("DELETE FROM commit_files")
    conn.execute("DELETE FROM commits")
    for c in commits:
        conn.execute(
            "INSERT OR REPLACE INTO commits (hash, author, email, committed_at, subject, body) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (c.hash, c.author, c.email, c.committed_at, c.subject, c.body),
        )
        for f in c.files:
            conn.execute(
                "INSERT OR REPLACE INTO commit_files (hash, path, status, additions, deletions) "
                "VALUES (?, ?, ?, ?, ?)",
                (c.hash, f.path, None, f.additions, f.deletions),
            )
    conn.commit()


def search_commits(conn: sqlite3.Connection, keyword: str) -> list[sqlite3.Row]:
    """依 message 或檔案路徑關鍵字找相關 commit,依時間新到舊排序。"""
    like = f"%{keyword}%"
    rows = conn.execute(
        """
        SELECT DISTINCT c.hash, c.author, c.committed_at, c.subject, c.body
        FROM commits c
        WHERE c.subject LIKE ? COLLATE NOCASE
           OR c.body LIKE ? COLLATE NOCASE
           OR c.hash IN (
               SELECT hash FROM commit_files WHERE path LIKE ? COLLATE NOCASE
           )
        ORDER BY c.committed_at DESC
        """,
        (like, like, like),
    ).fetchall()
    return rows


def files_for_commits(conn: sqlite3.Connection, hashes: list[str], top_n: int) -> list[sqlite3.Row]:
    """給定命中的 commit hash 集合,回傳這些 commit 裡出現過的檔案,依出現次數排序。"""
    if not hashes:
        return []
    placeholders = ",".join("?" for _ in hashes)
    rows = conn.execute(
        f"""
        SELECT path, COUNT(*) AS occurrences, MAX(hash) AS sample_hash
        FROM commit_files
        WHERE hash IN ({placeholders})
        GROUP BY path
        ORDER BY occurrences DESC, path ASC
        LIMIT ?
        """,
        (*hashes, top_n),
    ).fetchall()
    return rows


def files_for_commit(conn: sqlite3.Connection, chash: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT path, additions, deletions FROM commit_files WHERE hash = ? ORDER BY path",
        (chash,),
    ).fetchall()


def latest_commit_for_path(conn: sqlite3.Connection, path: str) -> str | None:
    row = conn.execute(
        """
        SELECT cf.hash FROM commit_files cf
        JOIN commits c ON c.hash = cf.hash
        WHERE cf.path = ?
        ORDER BY c.committed_at DESC LIMIT 1
        """,
        (path,),
    ).fetchone()
    return row["hash"] if row else None


def all_known_paths(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT path FROM commit_files").fetchall()
    return [r["path"] for r in rows]


def _self_check() -> None:
    conn = connect(":memory:")
    init_schema(conn)

    @dataclass
    class F:
        path: str
        additions: int | None
        deletions: int | None

    @dataclass
    class C:
        hash: str
        author: str
        email: str
        committed_at: str
        subject: str
        body: str
        files: list

    commits = [
        C("h1", "Alice", "a@x.com", "2024-01-02T00:00:00+08:00", "Fix auth bug", "detail",
          [F("src/auth/token.py", 3, 1)]),
        C("h2", "Bob", "b@x.com", "2024-01-01T00:00:00+08:00", "Add readme", "",
          [F("README.md", 10, 0), F("src/auth/token.py", 1, 0)]),
    ]
    index_repo(conn, commits)

    hits = search_commits(conn, "auth")
    assert [r["hash"] for r in hits] == ["h1", "h2"], hits

    files = files_for_commits(conn, ["h1", "h2"], top_n=10)
    assert files[0]["path"] == "src/auth/token.py" and files[0]["occurrences"] == 2, files

    assert latest_commit_for_path(conn, "src/auth/token.py") == "h1"
    assert [r["path"] for r in files_for_commit(conn, "h1")] == ["src/auth/token.py"]
    assert set(all_known_paths(conn)) == {"src/auth/token.py", "README.md"}

    print("db._self_check: OK")


if __name__ == "__main__":
    _self_check()
