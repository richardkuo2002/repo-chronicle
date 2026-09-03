"""no-network 保證是設計層級的事實(參見 README/SECURITY.md),用靜態原始碼檢查
驗證,而不是攔截真的網路呼叫——後者測不出「這支程式本來就不會連網」這件事,
只能測「這次剛好沒連」,沒有意義。"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src" / "repo_chronicle"

_NETWORK_MODULES = {
    "urllib",
    "requests",
    "socket",
    "http.client",
    "smtplib",
    "ftplib",
    "httpx",
    "aiohttp",
}


def _imported_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class NoNetworkImportsTest(unittest.TestCase):
    def test_no_source_file_imports_a_networking_module(self) -> None:
        py_files = sorted(_SRC_DIR.glob("*.py"))
        self.assertTrue(py_files, "expected to find source files under src/repo_chronicle")
        for py_file in py_files:
            imported = _imported_modules(py_file)
            hit = imported & _NETWORK_MODULES
            self.assertFalse(hit, f"{py_file} imports networking module(s): {hit}")


if __name__ == "__main__":
    unittest.main()
