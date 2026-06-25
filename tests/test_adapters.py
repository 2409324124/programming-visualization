import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.adapters import adapt_input, adapt_output
from pv.errors import AdapterError


class TestAdapters(unittest.TestCase):
    def test_builtin_pass_through_input(self):
        result = adapt_input({"nums": [1, 2]}, None)
        self.assertEqual(result, {"nums": [1, 2]})

    def test_builtin_pass_through_output(self):
        result = adapt_output([0, 1], None)
        self.assertEqual(result, [0, 1])

    def test_builtin_with_config(self):
        config = {"input": {"nums": {"kind": "builtin"}}, "output": {"kind": "builtin"}}
        result_in = adapt_input({"nums": [1, 2]}, config)
        self.assertEqual(result_in, {"nums": [1, 2]})
        result_out = adapt_output([0, 1], config)
        self.assertEqual(result_out, [0, 1])

    def test_unknown_kind_raises_input(self):
        config = {"input": {"head": {"kind": "graph"}}}
        with self.assertRaises(AdapterError):
            adapt_input({"head": [1]}, config)

    def test_unknown_kind_raises_output(self):
        config = {"output": {"kind": "graph"}}
        with self.assertRaises(AdapterError):
            adapt_output(None, config)

    def test_no_input_key_in_config(self):
        config = {"output": {"kind": "builtin"}}
        result = adapt_input({"a": 1}, config)
        self.assertEqual(result, {"a": 1})

    def test_missing_key_in_input(self):
        config = {"input": {"missing_key": {"kind": "builtin"}}}
        result = adapt_input({"nums": [1]}, config)
        self.assertEqual(result, {"nums": [1]})

    def test_adapter_error_user_message(self):
        try:
            config = {"input": {"head": {"kind": "graph"}}}
            adapt_input({"head": [1]}, config)
        except AdapterError as e:
            self.assertIn("不支持", e.user_message)


if __name__ == "__main__":
    unittest.main()
