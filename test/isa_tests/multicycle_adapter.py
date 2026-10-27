"""Model-specific interfaces; shared ISA build/protocol/reporting stay in tb_ISA_tests."""
from pathlib import Path
import re

import punxa_6502 as punxa


class MultiCycleAdapter:
    description = "Run 6502 ISA tests on MultiCycle6502 (CPU support is incomplete)."
    # Provisional finite ceiling, independently configurable; not a measured
    # budget for the blocked formal suite or original NMOS instruction cycles.
    max_cycles = 100000

    @staticmethod
    def create_cpu(hw, port, reset, irq, nmi, start):
        return punxa.MultiCycle6502(hw, "cpu", port, reset, irq, nmi, start)

    @staticmethod
    def pc(cpu):
        return cpu.children["datapath"]._wires["q_PC"].get()

    @staticmethod
    def clock(simulator):
        simulator.clk(1)

    @staticmethod
    def error_detail(exc):
        # Require the actual unhandled-opcode raise site, not just its text.
        expected = Path(punxa.__file__).parent / "structural/multicycle_processor.py"
        tb = exc.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        match = re.fullmatch(r"op ([0-9A-F]{2}) not handled", str(exc))
        if (match and tb is not None
                and Path(tb.tb_frame.f_code.co_filename).resolve() == expected.resolve()
                and tb.tb_frame.f_code.co_name == "decodeAndExecute"):
            return f"UNSUPPORTED_CPU: opcode=0x{match[1]} (no execution dispatch)"
        return f"{type(exc).__name__}: {exc}"
