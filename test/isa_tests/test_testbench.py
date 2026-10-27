"""Contract checks for the ISA testbench; no cc65 dependency."""
from contextlib import redirect_stdout, redirect_stderr
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import tb_ISA_tests as tb


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name in ("test_data_one.asm", "test_logic_two.ASM", "notes.inc"):
            (self.directory / name).write_text("")
        (self.directory / "nested").mkdir()
        (self.directory / "nested/test_data_hidden.asm").write_text("")

    def test_discovery_is_sorted_nonrecursive_and_assembly_only(self):
        self.assertEqual([p.name for p in tb.discover_tests(self.directory)],
                         ["test_data_one.asm", "test_logic_two.ASM"])

    def test_category_aliases_and_repeated_filters(self):
        for categories in ("data", ["test_data"], ["data", "test_data"]):
            self.assertEqual([p.name for p in tb.discover_tests(
                self.directory, categories)], ["test_data_one.asm"])
        self.assertEqual(len(tb.discover_tests(
            self.directory, ["data", "logic"])), 2)

    def test_unknown_category_is_an_error(self):
        with self.assertRaises(ValueError):
            tb.discover_tests(self.directory, ["missing"])

    def test_empty_directory_is_not_a_passing_suite(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                tb.discover_tests(directory)

    def test_unconventional_asm_name_is_uncategorized(self):
        (self.directory / "plain.asm").write_text("")
        self.assertEqual([p.name for p in tb.discover_tests(
            self.directory, "uncategorized")], ["plain.asm"])

    def test_list_does_not_build_or_simulate(self):
        with patch.object(tb, "build_test", side_effect=AssertionError("built")):
            output = io.StringIO()
            with redirect_stdout(output):
                code = tb.main(["--list", "--test-dir", str(self.directory)])
        self.assertEqual(code, 0)
        self.assertIn("test_logic_two.ASM", output.getvalue())


class ExecutionTests(unittest.TestCase):
    def execute(self, states, limit=10, error=None):
        memory = {11: 7, 12: 0}
        cpu = SimpleNamespace(pc=512, retired=0)
        cpu.getRetiredInstructions = lambda: cpu.retired
        sequence = iter(states)

        def clock(count):
            if error is not None:
                raise error
            try:
                cpu.retired, cpu.pc, memory[12] = next(sequence)
            except StopIteration:
                pass

        simulator = SimpleNamespace(clk=clock)
        hw = SimpleNamespace(getSimulator=lambda: simulator)
        mem = SimpleNamespace(readByte=lambda address: memory[address])
        return tb.execute_test(hw, cpu, mem,
                               {"test_case": 11, "final_result": 12, "end": 600},
                               "test_data_contract.asm", limit)

    def test_end_must_be_reached_at_instruction_retirement(self):
        result = self.execute([(0, 600, 1), (1, 590, 1), (2, 600, 1)])
        self.assertEqual((result.outcome, result.cycles), ("PASS", 3))

    def test_strict_final_status(self):
        for status, outcome in ((1, "PASS"), (255, "FAIL"),
                                (0, "ERROR"), (2, "ERROR"), (254, "ERROR")):
            with self.subTest(status=status):
                result = self.execute([(1, 600, status)])
                self.assertEqual(result.outcome, outcome)
                if outcome == "ERROR":
                    self.assertIn("PROTOCOL ERROR", result.detail)

    def test_early_success_without_end_times_out(self):
        result = self.execute([(1, 590, 1)], limit=4)
        self.assertEqual((result.outcome, result.cycles), ("TIMEOUT", 4))

    def test_simulator_exception_becomes_error(self):
        result = self.execute([], error=RuntimeError("injected failure"))
        self.assertEqual(result.outcome, "ERROR")
        self.assertIn("injected failure", result.detail)


class ReportingTests(unittest.TestCase):
    def test_all_outcomes_and_category_totals_are_counted(self):
        results = {str(i): tb.TestResult(str(i), category, outcome)
                   for i, (category, outcome) in enumerate([
                       ("test_data", "PASS"), ("test_data", "FAIL"),
                       ("test_logic", "TIMEOUT"), ("test_logic", "ERROR"),
                       ("test_logic", "PASS")])}
        summary = tb.summarize_results(results)
        self.assertEqual(summary["total"],
                         {"PASS": 2, "FAIL": 1, "TIMEOUT": 1, "ERROR": 1,
                          "total": 5, "pass_rate": 40.0})
        self.assertEqual(summary["categories"]["test_data"]["total"], 2)

    def test_single_file_boolean_api_is_preserved(self):
        for outcome in ("PASS", "FAIL", "TIMEOUT", "ERROR"):
            with patch.object(tb, "run_file_result",
                              return_value=tb.TestResult("test.asm", "test", outcome)):
                with redirect_stdout(io.StringIO()):
                    self.assertIs(tb.run_file("test.asm"), outcome == "PASS")

    def test_cli_rejects_mixed_single_and_batch_selection(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                tb.main(["test_data_LDA", "--all"])
        self.assertEqual(caught.exception.code, 2)

    def test_avr_command_option_accepts_only_supported_literal(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                tb.main(["-c", "unsupported()"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
