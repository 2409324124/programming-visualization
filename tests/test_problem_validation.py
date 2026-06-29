import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


ROOT = Path(__file__).resolve().parent.parent
TWO_SUM_DIR = ROOT / "problems" / "0001_two_sum"
PROBLEM_IDS = [
    "0001_two_sum",
    "0011_container_with_most_water",
    "0070_climbing_stairs",
    "0198_house_robber",
    "0206_reverse_linked_list",
]


def _valid_pairs(nums, target):
    pairs = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                pairs.append([i, j])
    return pairs


class TestTwoSumProblemValidation(unittest.TestCase):
    def test_two_sum_oracle_returns_indices(self):
        from pv.problem_validation import two_sum_oracle

        self.assertEqual(two_sum_oracle([2, 7, 11, 15], 9), [0, 1])
        self.assertEqual(two_sum_oracle([-1, -2, -3, -4, -5], -8), [2, 4])

    def test_two_sum_oracle_uses_bruteforce_pair_order(self):
        from pv.problem_validation import two_sum_oracle

        # Brute force checks pairs as (0,1), (0,2), ...
        # A hash-map scan would return [1, 2] for this input.
        self.assertEqual(two_sum_oracle([1, 2, 3], 4), [0, 2])

    def test_generated_two_sum_cases_are_deterministic_and_unique(self):
        from pv.problem_validation import generate_two_sum_cases

        cases1 = generate_two_sum_cases(25, seed=0)
        cases2 = generate_two_sum_cases(25, seed=0)
        self.assertEqual(cases1, cases2)
        self.assertEqual(len(cases1), 25)
        for case in cases1:
            self.assertIn("args", case)
            self.assertIn("expected", case)
            nums = case["args"]["nums"]
            target = case["args"]["target"]
            self.assertEqual(_valid_pairs(nums, target), [case["expected"]])

    def test_validate_problem_passes_fixed_and_generated_cases(self):
        from pv.problem_validation import validate_problem

        result = validate_problem(str(TWO_SUM_DIR), generated_count=20, seed=0)
        self.assertTrue(result["passed"])
        self.assertEqual(result["fixed"]["passed"], result["fixed"]["total"])
        self.assertEqual(result["generated"]["passed"], 20)
        self.assertIsNone(result["first_failure"])

    def test_validate_problem_reports_first_failure(self):
        from pv.problem_validation import validate_problem

        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(TWO_SUM_DIR / "problem.json", tmpdir)
            shutil.copy(TWO_SUM_DIR / "cases.json", tmpdir)
            with open(os.path.join(tmpdir, "solution.py"), "w", encoding="utf-8") as f:
                f.write(
                    """
class Solution:
    def twoSum(self, nums, target):
        return [0, 0]
"""
                )

            result = validate_problem(tmpdir, generated_count=5, seed=0)
            self.assertFalse(result["passed"])
            failure = result["first_failure"]
            self.assertIsNotNone(failure)
            self.assertIn("args", failure["case"])
            self.assertIn("expected", failure["result"])
            self.assertIn("actual", failure["result"])

    def test_unsupported_problem_is_rejected(self):
        from pv.problem_validation import ProblemValidationError, validate_problem

        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(TWO_SUM_DIR / "problem.json", os.path.join(tmpdir, "problem.json"))
            shutil.copy(TWO_SUM_DIR / "cases.json", os.path.join(tmpdir, "cases.json"))
            with open(os.path.join(tmpdir, "problem.json"), "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["problem_id"] = "9999_unknown"
            with open(os.path.join(tmpdir, "problem.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f)
            shutil.copy(TWO_SUM_DIR / "solution.py", os.path.join(tmpdir, "solution.py"))

            with self.assertRaises(ProblemValidationError):
                validate_problem(tmpdir, generated_count=1, seed=0)


class TestProblemValidationRegistry(unittest.TestCase):
    def test_oracles_return_independent_expected_values(self):
        from pv.problem_validation import (
            climbing_stairs_oracle,
            container_with_most_water_oracle,
            house_robber_oracle,
            reverse_linked_list_oracle,
        )

        self.assertEqual(container_with_most_water_oracle([1, 8, 6, 2, 5, 4, 8, 3, 7]), 49)
        self.assertEqual(container_with_most_water_oracle([5, 5, 5, 5]), 15)
        self.assertEqual(climbing_stairs_oracle(1), 1)
        self.assertEqual(climbing_stairs_oracle(2), 2)
        self.assertEqual(climbing_stairs_oracle(10), 89)
        self.assertEqual(house_robber_oracle([]), 0)
        self.assertEqual(house_robber_oracle([2, 7, 9, 3, 1]), 12)
        self.assertEqual(house_robber_oracle([100, 1, 1, 100]), 200)
        self.assertEqual(reverse_linked_list_oracle([]), [])
        self.assertEqual(reverse_linked_list_oracle([1, 2, 3]), [3, 2, 1])

    def test_generated_cases_are_deterministic_and_use_oracles(self):
        from pv.problem_validation import (
            climbing_stairs_oracle,
            container_with_most_water_oracle,
            generate_climbing_stairs_cases,
            generate_container_with_most_water_cases,
            generate_house_robber_cases,
            generate_reverse_linked_list_cases,
            house_robber_oracle,
            reverse_linked_list_oracle,
        )

        generator_specs = [
            (
                generate_container_with_most_water_cases,
                "height",
                container_with_most_water_oracle,
            ),
            (generate_climbing_stairs_cases, "n", climbing_stairs_oracle),
            (generate_house_robber_cases, "nums", house_robber_oracle),
            (generate_reverse_linked_list_cases, "head", reverse_linked_list_oracle),
        ]

        for generator, arg_name, oracle in generator_specs:
            with self.subTest(generator=generator.__name__):
                cases1 = generator(25, seed=0)
                cases2 = generator(25, seed=0)
                self.assertEqual(cases1, cases2)
                self.assertEqual(len(cases1), 25)
                for case in cases1:
                    value = case["args"][arg_name]
                    self.assertEqual(case["expected"], oracle(value))

    def test_validate_problem_supports_all_current_problems(self):
        from pv.problem_validation import validate_problem

        for problem_id in PROBLEM_IDS:
            with self.subTest(problem_id=problem_id):
                result = validate_problem(
                    str(ROOT / "problems" / problem_id),
                    generated_count=20,
                    seed=0,
                )
                self.assertTrue(result["passed"])
                self.assertEqual(result["fixed"]["passed"], result["fixed"]["total"])
                self.assertEqual(result["generated"]["passed"], 20)
                self.assertIsNone(result["first_failure"])

    def test_validate_problem_supports_visual_solutions_for_all_current_problems(self):
        from pv.problem_validation import validate_problem

        for problem_id in PROBLEM_IDS:
            with self.subTest(problem_id=problem_id):
                result = validate_problem(
                    str(ROOT / "problems" / problem_id),
                    generated_count=10,
                    seed=0,
                    solution_file="visual_solution.py",
                )
                self.assertTrue(result["passed"])
                self.assertEqual(result["generated"]["passed"], 10)


class TestValidateProblemCli(unittest.TestCase):
    def _run_cli(self, argv):
        from pv.cli import main

        old_argv = sys.argv[:]
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            sys.argv = argv
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    main()
                except SystemExit as exc:
                    code = exc.code if isinstance(exc.code, int) else 1
                else:
                    code = 0
        finally:
            sys.argv = old_argv
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_validate_problem_success(self):
        code, stdout, stderr = self._run_cli([
            "pv",
            "validate-problem",
            str(TWO_SUM_DIR),
            "--generated",
            "5",
            "--seed",
            "0",
        ])

        self.assertEqual(code, 0, stderr)
        self.assertIn("fixed:", stdout)
        self.assertIn("generated: 5/5 passed", stdout)
        self.assertIn("total:", stdout)

    def test_cli_validate_problem_failure_prints_details(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(TWO_SUM_DIR / "problem.json", tmpdir)
            shutil.copy(TWO_SUM_DIR / "cases.json", tmpdir)
            with open(os.path.join(tmpdir, "solution.py"), "w", encoding="utf-8") as f:
                f.write(
                    """
class Solution:
    def twoSum(self, nums, target):
        return [0, 0]
"""
                )

            code, stdout, stderr = self._run_cli([
                "pv",
                "validate-problem",
                tmpdir,
                "--generated",
                "5",
                "--seed",
                "0",
            ])

        self.assertEqual(code, 1)
        combined = stdout + stderr
        self.assertIn("first failure", combined)
        self.assertIn("input:", combined)
        self.assertIn("expected:", combined)
        self.assertIn("actual:", combined)


if __name__ == "__main__":
    unittest.main()
