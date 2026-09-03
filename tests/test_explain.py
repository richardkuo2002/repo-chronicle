"""explain.py 測試:包既有的 _self_check() 邏輯,讓 unittest discover 抓得到。"""
from __future__ import annotations

import unittest

from repo_chronicle import explain


class ExplainSelfCheckTest(unittest.TestCase):
    def test_self_check(self) -> None:
        explain._self_check()


if __name__ == "__main__":
    unittest.main()
