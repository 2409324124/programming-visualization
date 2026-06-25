import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.checkers import check, CheckResult
from pv.errors import CheckerError


class TestCheckers(unittest.TestCase):
    def test_exact_pass(self):
        r = check([0, 1], [0, 1], "exact")
        self.assertTrue(r.passed)
        self.assertIn("一致", r.message)

    def test_exact_fail(self):
        r = check([0, 1], [1, 0], "exact")
        self.assertFalse(r.passed)
        self.assertIn("不符", r.message)

    def test_exact_int_pass(self):
        r = check(42, 42, "exact")
        self.assertTrue(r.passed)

    def test_exact_string_pass(self):
        r = check("hello", "hello", "exact")
        self.assertTrue(r.passed)

    def test_unordered_pairs_pass(self):
        r = check([[0, 1]], [[1, 0]], "unordered_pairs")
        self.assertTrue(r.passed)
        self.assertIn("顺序", r.message)

    def test_unordered_pairs_multiple(self):
        r = check([[0, 1], [2, 3]], [[3, 2], [1, 0]], "unordered_pairs")
        self.assertTrue(r.passed)

    def test_unordered_pairs_fail(self):
        r = check([[0, 1]], [[0, 2]], "unordered_pairs")
        self.assertFalse(r.passed)

    def test_unknown_checker_raises(self):
        with self.assertRaises(CheckerError):
            check(1, 1, "not_exist")

    def test_default_checker_is_exact(self):
        r = check(1, 1)
        self.assertTrue(r.passed)

    def test_check_result_fields(self):
        r = check([0, 1], [0, 1], "exact")
        self.assertIsInstance(r.passed, bool)
        self.assertEqual(r.expected, [0, 1])
        self.assertEqual(r.actual, [0, 1])
        self.assertIsInstance(r.message, str)


if __name__ == "__main__":
    unittest.main()
