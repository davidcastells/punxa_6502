"""Regression test: SingleCycle DEC of $00 must leave N exactly 1.

DEC used to compute R = w - 1 without masking, so $00 - 1 gave R = -1 and
N = -1 >> 7 = -1. Memory and the PHP byte still looked correct because py4hw
masks values written to 8-bit wires, so the .asm ISA test cannot see this bug.
This test checks the internal flag values directly.
"""
import contextlib
import io
import unittest

import py4hw
import punxa_6502 as punxa
from punxa_6502.assembly import assemble_program

ORIGIN = 0x0200
MAX_STEPS = 100

# (mode, opcode, setup X, DEC operand, effective address)
CASES = (
    ("zp",    0xC6, 0x00, "$40",      0x0040),
    ("zp,X",  0xD6, 0x02, "$40,x",    0x0042),
    ("abs",   0xCE, 0x00, "$1000",    0x1000),
    ("abs,X", 0xDE, 0x01, "$10FF,x",  0x1100),  # crosses a page
)


def program(index_x, operand, target):
    return f"""
.export start, probe, end
start:
    ldx #$FF
    txs
    cld
    clc
    ldx #${index_x:02X}
    lda #$00
    sta ${target:04X}   ; operand byte = $00; also seeds Z=1, N=0 (opposite of expected)
probe:
    dec {operand}
    php                 ; pushes P to $01FF
end:
    jmp end
"""


def run(source):
    assembled = assemble_program(source, origin=ORIGIN)
    symbols = dict(assembled.symbols)

    hw = py4hw.HWSystem()
    reset, irq, nmi = hw.wire("reset"), hw.wire("irq"), hw.wire("nmi")
    cpu_port = punxa.MemoryInterface(hw, "cpu_port", 8, 16)
    mem_port = punxa.MemoryInterface(hw, "mem_port", 8, 22)
    mem = punxa.SparseMemory(hw, "main_memory", 8, 32, mem_port, mem_base=0)
    punxa.MultiplexedBus(hw, "bus", cpu_port, [(mem_port, 0)])
    cpu = punxa.SingleCycle6502(hw, "cpu", cpu_port, reset, irq, nmi, ORIGIN)
    cpu.loadSymbols(symbols)
    mem.reallocArea(0, 0x10000, verbose=False)
    for offset, byte in enumerate(assembled.code):
        mem.writeByte(ORIGIN + offset, byte)

    sim = hw.getSimulator()
    with contextlib.redirect_stdout(io.StringIO()):  # hide the CPU trace
        for _ in range(MAX_STEPS):
            if cpu.getRegister("PC") == symbols["end"]:
                break
            retired = cpu.getRetiredInstructions()
            while cpu.getRetiredInstructions() == retired:
                sim.clk(1)
        else:
            raise AssertionError("program did not reach 'end'")
    return cpu, mem, symbols


class SingleCycleDecZeroTests(unittest.TestCase):
    def test_dec_of_zero_sets_n_to_exactly_one(self):
        for mode, opcode, index_x, operand, target in CASES:
            with self.subTest(mode=mode):
                cpu, mem, symbols = run(program(index_x, operand, target))
                # The intended addressing mode was really executed.
                self.assertEqual(mem.readByte(symbols["probe"]), opcode)
                # Internal flags: exactly 1 and 0, not merely "truthy".
                self.assertEqual(cpu.N, 1)
                self.assertEqual(cpu.Z, 0)
                # Memory result: $00 - 1 wraps to $FF.
                self.assertEqual(mem.readByte(target), 0xFF)
                # PHP byte: N=1, V=0, bit5=1, B=1, D=0, I=0, Z=0, C=0.
                self.assertEqual(mem.readByte(0x01FF), 0xB0)


if __name__ == "__main__":
    unittest.main()
