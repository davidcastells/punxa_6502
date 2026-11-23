"""Test-only bus monitor for memory side effects of read-modify-write probes.

A test opts in by exporting, for each instruction to be monitored, a label and
a constant holding the effective operand address of that instruction:

    asl_stk_probe_5:            ; label on the target instruction
        asl $01FE
    asl_stk_probe_5_ea = $01FE  ; effective address (exported)

While the instruction at a probe label executes, every clock samples the CPU
memory port (read/write enable, address, data). The rules checked are:

  * no write to any address other than the effective address;
  * the operand is read before anything is written to the effective address
    (a write of A to the operand before it is read is a side effect);
  * the effective address is read and written at least once.

The number of reads/writes is not constrained (dummy RMW writes are allowed).
Every declared probe must also execute exactly once in a passing run
(coverage_errors()), so a skipped or misplaced probe label cannot pass silently.
Tests without *_ea symbols are not affected: steps are then plain step() calls.

Sampling: in py4hw a clk() runs every clock() (memory included) on the current
wire values and then settles the prepared ones, so the port state read after
clk() is exactly the request memory serves on the next clock. Read data is not
recorded, and back-to-back identical requests with no idle clock in between
count as one transaction.
"""

import punxa_6502 as punxa
from punxa_6502.interactive_commands import MAX_CLOCKS_PER_INSTRUCTION


class SideEffectMonitor:

    def __init__(self, cpu, symbols):
        self.cpu = cpu
        self.port = cpu.mem                      # the CPU-side MemoryInterface
        self.probes = {}                         # pc -> (label, effective address)
        for name, value in symbols.items():
            if name.endswith('_ea') and name[:-3] in symbols:
                pc = symbols[name[:-3]]
                if pc in self.probes:
                    raise Exception(f'probes {self.probes[pc][0]} and {name[:-3]} '
                                    f'share address ${pc:04X}')
                self.probes[pc] = (name[:-3], value)
        self.executions = {label: 0 for label, _ in self.probes.values()}
        self.records = []                        # one entry per executed probe
        self.violations = []

    def step(self, plain_step):
        """Execute one instruction; monitor the bus if it is a probe."""
        pc = self.cpu.getRegister('PC')
        if pc not in self.probes:
            plain_step()
            return
        label, ea = self.probes[pc]
        self.executions[label] += 1
        events = self._monitored_step()
        record = dict(label=label, pc=pc, ea=ea, events=events,
                      instruction=self._disassemble(pc))
        record['violations'] = self._check(ea, events)
        self.records.append(record)
        for v in record['violations']:
            self.violations.append(f"{label} [{record['instruction']}]: {v}")

    def coverage_errors(self):
        """Probes not executed exactly once ([] when no probes are declared)."""
        return [f'{label} executed {n} times (expected 1)'
                for label, n in sorted(self.executions.items()) if n != 1]

    def describe(self):
        """Text appended to a failure message ('' when nothing was detected)."""
        if not self.violations:
            return ''
        lines = ['', 'Unintended memory side effects:']
        lines += ['  ' + v for v in self.violations]
        for r in self.records:
            if r['violations']:
                trace = ' '.join(f"{k}[{a:04X}]={d:02X}" for k, a, d in r['events'])
                lines.append(f"  bus trace {r['label']}: {trace}")
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    def _monitored_step(self):
        sim = self.cpu.parent.getSimulator()
        port = self.port
        retired = self.cpu.getRetiredInstructions()
        events = []                              # ('R'|'W', address, data)
        clocks = 0
        last_idle = True
        while retired == self.cpu.getRetiredInstructions():
            sim.clk()
            clocks += 1
            if clocks > MAX_CLOCKS_PER_INSTRUCTION:
                raise Exception('CPU did not retire an instruction after '
                                f'{MAX_CLOCKS_PER_INSTRUCTION} clocks')
            if port.write.get():
                ev = ('W', port.address.get(), port.write_data.get())
            elif port.read.get():
                ev = ('R', port.address.get(), 0)
            else:
                ev = None
            # an access held for several clocks is one bus transaction
            if ev is not None and (not events or events[-1] != ev or last_idle):
                events.append(ev)
            last_idle = ev is None
        return events

    def _check(self, ea, events):
        problems = []
        read_seen = False
        for kind, address, data in events:
            if kind == 'R' and address == ea:
                read_seen = True
            elif kind == 'W' and address != ea:
                problems.append(f'unexpected write ${address:04X}=${data:02X} '
                                f'(effective address ${ea:04X})')
            elif kind == 'W' and not read_seen:
                problems.append(f'write ${address:04X}=${data:02X} before the '
                                'operand was read')
        if not read_seen:
            problems.append(f'operand ${ea:04X} was never read')
        if not any(k == 'W' and a == ea for k, a, _ in events):
            problems.append(f'result was never written to ${ea:04X}')
        return problems

    def _disassemble(self, pc):
        mem = self._memory()
        op = mem.readByte(pc)
        ins, mode = punxa.ins_to_str(op)
        n = punxa.OPERAND_SIZE_MAP[mode]
        operand = 0
        for i in range(n):
            operand |= mem.readByte(pc + 1 + i) << (8 * i)
        text = f'{op:02X} {ins} {mode}'
        if n:
            text += f' ${operand:0{2 * n}X}'
        return text

    def _memory(self):
        import punxa_6502.interactive_commands as ci
        return ci._ci_mem
