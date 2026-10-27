"""Focused adapter contracts; synthetic outcomes are not ISA execution results."""
from types import SimpleNamespace
import unittest

import tb_ISA_tests as shared
from multicycle_adapter import MultiCycleAdapter


class AdapterTests(unittest.TestCase):
    def execute(self, status, limit=3, error=None):
        values = {"pc": 512, "retired": 0, "status": 0}
        cpu = SimpleNamespace(children={"datapath": SimpleNamespace(
            _wires={"q_PC": SimpleNamespace(get=lambda: values["pc"])})},
            getRetiredInstructions=lambda: values["retired"])
        sequence = iter([(0, 600), (1, 590), (2, 600)])

        def clock(count):
            if error:
                raise error
            values["retired"], values["pc"] = next(sequence)
            values["status"] = status

        hw = SimpleNamespace(getSimulator=lambda: SimpleNamespace(clk=clock))
        memory = SimpleNamespace(readByte=lambda address: values["status"] if address == 12 else 7)
        return shared.execute_test(hw, cpu, memory,
                                   {"test_case": 11, "final_result": 12, "end": 600},
                                   max_cycles=limit, adapter=MultiCycleAdapter())

    def test_strict_status_and_retirement_boundary(self):
        for status, outcome in ((1, "PASS"), (255, "FAIL"), (0, "ERROR"), (2, "ERROR")):
            with self.subTest(status=status):
                result = self.execute(status)
                self.assertEqual((result.outcome, result.cycles, result.retired), (outcome, 3, 2))

    def test_pc_at_end_before_retirement_does_not_pass(self):
        result = self.execute(1, limit=1)
        self.assertEqual((result.outcome, result.retired), ("TIMEOUT", 0))

    def test_exception_text_alone_is_not_unsupported(self):
        result = self.execute(1, error=RuntimeError("op D8 not handled"))
        self.assertEqual(result.outcome, "ERROR")
        self.assertNotIn("UNSUPPORTED_CPU", result.detail)

    def test_other_runtime_error_stays_error(self):
        result = self.execute(1, error=KeyError("missing signal"))
        self.assertIn("KeyError", result.detail)
        self.assertNotIn("UNSUPPORTED_CPU", result.detail)


if __name__ == "__main__":
    unittest.main()
