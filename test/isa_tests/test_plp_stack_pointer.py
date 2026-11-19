"""Testbench check of the stack pointer immediately after PLP, on the SingleCycle
and Hybrid models. The Microcoded model is not run: it has no retired-instruction
counter yet, so step() cannot drive it.

isa/test_data_PLP.asm can only observe SP through TSX and a store, and every
store goes through the 8-bit data bus. An SP that wrongly becomes $100 instead
of wrapping to $00 is therefore stored as $00 and passes the ISA-level check
(case 15). This test reads the CPU's own SP register right after each PLP probe
in that file, where no truncation happens, and also checks the pulled byte and
the decoy at the not-pulled stack slot. It then runs the program to the end.
"""
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tb_ISA_tests
import tb_ISA_tests_Hybrid

TEST_FILE = 'test_data_PLP.asm'
STEP_LIMIT = 20000

# probe label: (SP before PLP, SP after PLP, pulled address, pulled byte, other slot, other byte)
PROBES = {
    'plp_probe_13': (0xFF, 0x00, 0x0100, 0xC3, 0x01FF, 0x5D),
    'plp_probe_14': (0xFE, 0xFF, 0x01FF, 0x96, 0x0100, 0x22),
    'plp_probe_15': (0xFF, 0x00, 0x0100, 0x69, 0x01FF, 0x5D),
}


def run_and_record(runner):
    """Run the PLP test, stepping one instruction at a time; record state at each probe."""
    runner.prepareTest(TEST_FILE)
    cpu, mem, symbols = runner.cpu, runner.mem, runner.symbols
    probes = {symbols[name]: name for name in PROBES}
    seen = {}
    steps = 0
    with contextlib.redirect_stdout(io.StringIO()):
        while cpu.getRegister('PC') != symbols['end']:
            pc = cpu.getRegister('PC')
            if pc in probes:
                sp_before = cpu.getRegister('SP')
                runner.step()  # execute exactly the PLP
                _, _, pulled_addr, _, other_addr, _ = PROBES[probes[pc]]
                seen[probes[pc]] = (sp_before, cpu.getRegister('SP'),
                                    mem.readByte(pulled_addr), mem.readByte(other_addr))
            else:
                runner.step()
            # Checked after every step, including a PLP probe: a PLP that does not
            # advance PC would otherwise repeat forever at the same probe.
            steps += 1
            if steps > STEP_LIMIT:
                raise AssertionError('step limit exceeded')
    return seen, mem.readByte(symbols['final_result']), mem.readByte(symbols['test_case'])


class PlpStackPointerTests(unittest.TestCase):
    def check_model(self, runner):
        seen, final_result, test_case = run_and_record(runner)
        self.assertEqual(set(seen), set(PROBES), 'every PLP probe must be reached')
        for name, (sp_before, sp_after, pulled_addr, pulled, other_addr, other) in PROBES.items():
            got_before, got_after, got_pulled, got_other = seen[name]
            with self.subTest(probe=name):
                self.assertEqual(got_before, sp_before, 'SP before PLP')
                self.assertEqual(got_after, sp_after, 'SP immediately after PLP')
                self.assertEqual(got_pulled, pulled, f'pulled byte at ${pulled_addr:04X} unchanged')
                self.assertEqual(got_other, other, f'byte at ${other_addr:04X} unchanged')
        self.assertEqual(final_result, 1, f'ISA test failed in case {test_case}')

    def test_singlecycle(self):
        self.check_model(tb_ISA_tests)

    def test_hybrid(self):
        self.check_model(tb_ISA_tests_Hybrid)


if __name__ == '__main__':
    unittest.main()
