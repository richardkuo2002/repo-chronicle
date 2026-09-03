"""render.py 的純單元測試:不需要真的 git repo,直接組假資料丟進 render()。"""
from __future__ import annotations

import unittest

from repo_chronicle.explain import AffectedFile, CommitEntry, ExplainResult
from repo_chronicle.render import _code_span, _escape_backticks, _table_cell, render


class CodeSpanTest(unittest.TestCase):
    def test_normal_text_is_byte_identical_to_old_hardcoded_backticks(self) -> None:
        # 沒有反引號時,新版 helper 產生的結果要跟原本寫死的 f"`{x}`" 完全一樣,
        # 確保一般輸入(v1 就有的案例)輸出不變。
        self.assertEqual(_code_span("src/auth/token.py"), "`src/auth/token.py`")
        self.assertEqual(_code_span("a1b2c3d1e2"), "`a1b2c3d1e2`")

    def test_single_backtick_gets_longer_fence_and_padding(self) -> None:
        result = _code_span("weird`path")
        self.assertNotIn("``weird`path``".replace("``", "`", 1), [result])  # 不是天真包法
        # 定界符要比內容裡最長的連續反引號還長,且不會被內容裡的反引號提前結束。
        self.assertTrue(result.startswith("``"))
        self.assertTrue(result.endswith("``"))
        self.assertIn("weird`path", result)

    def test_leading_backtick_gets_padding_space(self) -> None:
        result = _code_span("`leading")
        # CommonMark 規則:內容以反引號開頭時,定界符與內容間要有空白,否則會黏在一起。
        self.assertTrue(result.startswith("`` `"))

    def test_newline_is_flattened_to_space(self) -> None:
        self.assertNotIn("\n", _code_span("a\nb"))


class EscapeBacktickTest(unittest.TestCase):
    def test_no_backtick_is_unchanged(self) -> None:
        self.assertEqual(_escape_backticks("normal subject"), "normal subject")

    def test_backtick_is_escaped(self) -> None:
        self.assertEqual(_escape_backticks("weird`backtick`text"), "weird\\`backtick\\`text")


class TableCellTest(unittest.TestCase):
    def test_normal_text_is_byte_identical_to_code_span(self) -> None:
        self.assertEqual(_table_cell("src/auth/token.py"), "`src/auth/token.py`")

    def test_pipe_falls_back_to_escaped_plain_text_not_code_span(self) -> None:
        result = _table_cell("src/weird|dir/a.py")
        self.assertEqual(result, "src/weird\\|dir/a.py")
        self.assertNotIn("`", result)  # 含 | 時刻意不包 code span,見 render.py 說明

    def test_backslash_is_escaped(self) -> None:
        self.assertEqual(_table_cell("a|b\\c"), "a\\|b\\\\c")


class RenderIntegrationTest(unittest.TestCase):
    def _result(self, commits, affected_files) -> ExplainResult:
        return ExplainResult(keyword="auth", commits=commits, affected_files=affected_files)

    def test_adversarial_commit_data_produces_well_formed_markdown(self) -> None:
        commits = [
            CommitEntry(
                hash="deadbeef01",
                author="A",
                committed_at="2024-01-01T00:00:00+00:00",
                subject="weird `backtick` and | pipe in message",
                body="",
                files=[{"path": "src/weird|dir/a.py", "additions": 1, "deletions": 0}],
            ),
            CommitEntry(
                hash="deadbeef02",
                author="A",
                committed_at="2024-01-02T00:00:00+00:00",
                subject="odd backtick ` in message",
                body="",
                files=[],
            ),
        ]
        affected = [
            AffectedFile(
                path="src/weird|dir/a.py",
                occurrences=1,
                sample_hash="deadbeef01",
                test_candidates=[],
            )
        ]
        output = self._result(commits, affected)
        md = render(output, "/tmp/repo")

        # 表格結構完整:affected-files 表的資料列要剛好 3 欄(前後含邊界 |)。
        # 跳脫掉的 \| 不算欄位分隔,只數「沒有被反斜線跳脫」的 |。
        table_row = next(line for line in md.splitlines() if line.startswith("| src") or line.startswith("| `src"))
        unescaped_pipes = table_row.count("|") - table_row.count("\\|")
        self.assertEqual(unescaped_pipes, 4, table_row)  # | cell | cell | cell |

        # 不應該有「奇數反引號」殘留,否則代表 code span 沒有正確配對。
        # 先把 \` (跳脫過的字面反引號,本來就不是 fence 的一部分)拿掉,剩下的
        # 才是真正的 code span 定界符,必須成對出現。
        remaining_backticks = md.replace("\\`", "")
        self.assertEqual(
            remaining_backticks.count("`") % 2, 0,
            "反引號數量必須成對,否則 code span 會吃掉後面內容",
        )

        # 原始內容(去除跳脫)還是要看得到,不能被整段拿掉或摘要。
        self.assertIn("backtick", md)
        self.assertIn("pipe in message", md)
        self.assertIn("odd backtick", md)

    def test_normal_input_output_unchanged_shape(self) -> None:
        commits = [
            CommitEntry(
                hash="abc123abcd",
                author="Alice",
                committed_at="2024-01-02T00:00:00+00:00",
                subject="Fix auth token",
                body="detail",
                files=[{"path": "src/auth/token.py", "additions": 3, "deletions": 1}],
            ),
        ]
        affected = [
            AffectedFile(
                path="src/auth/token.py",
                occurrences=1,
                sample_hash="abc123abcd",
                test_candidates=["tests/auth/test_token.py"],
            )
        ]
        md = render(self._result(commits, affected), "/tmp/repo")

        self.assertIn("# Context Pack: auth", md)
        self.assertIn("## 演進脈絡(依時間排序)", md)
        self.assertIn("### 2024-01-02 `abc123abcd` — Fix auth token", md)
        self.assertIn("- `src/auth/token.py` (+3/-1)", md)
        self.assertIn("| `src/auth/token.py` | 1 | `abc123abcd` |", md)
        self.assertIn("- `tests/auth/test_token.py`(對應 `src/auth/token.py`)", md)
        self.assertIn("## 附註", md)


if __name__ == "__main__":
    unittest.main()
