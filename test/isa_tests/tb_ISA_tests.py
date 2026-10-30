"""Assemble and run self-checking 6502 tests in Python using exported symbols."""

import argparse
from collections import Counter
from contextlib import redirect_stdout
from dataclasses import dataclass
import io
from pathlib import Path
import sys

import py4hw
import punxa_6502 as punxa
from punxa_6502.assembly import AssemblyResult, assemble_file


TEST_DIR = Path(__file__).resolve().parent
# Explicit legacy file loading remains available through prepare_test().
TEST_FILE = TEST_DIR / "test_data_LDA.bin"
SYMBOL_FILE = TEST_DIR / "test_data_LDA.lbl"
PROGRAM_START = 0x0200
MEMORY_SIZE = 0x10000
PROTOCOL_SYMBOLS = ("test_case", "final_result", "end")
# Timing-only 32-case diagnostic measured 5281 clocks; retain finite headroom.
MAX_CYCLES = 10000


def _validate_symbols(symbols, exports):
    """Require exported, byte-addressed protocol symbols before constructing CPUs."""
    for name in PROTOCOL_SYMBOLS:
        if name not in exports or name not in symbols:
            raise ValueError(f"Missing exported symbol: {name}")
        if type(symbols[name]) is not int or not 0 <= symbols[name] < MEMORY_SIZE:
            raise ValueError(f"Symbol outside 6502 memory or not an integer: {name}")


def read_symbols(path):
    """Read an explicitly supplied legacy VICE label file; not used by normal runs."""
    symbols = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[0] == "al":
            name = fields[2].removeprefix(".")
            if name in symbols:
                raise ValueError(f"Duplicate exported symbol: {name}")
            symbols[name] = int(fields[1], 16)
    _validate_symbols(symbols, symbols)
    return symbols


def prepare_program(program: AssemblyResult, *, adapter=None):
    """Validate in-memory assembly and load it into fresh CPU/64 KiB memory.

    The assembler enforces its CODE layout limits. This loader also validates
    arbitrary AssemblyResult inputs against simulated memory and protocol slots.
    Returned symbols are copied so callers cannot mutate the assembly result.
    """
    if not isinstance(program, AssemblyResult):
        raise TypeError("prepare_program requires an AssemblyResult")
    if not isinstance(program.code, bytes):
        raise ValueError("Test program must contain machine-code bytes")
    if not program.code:
        raise ValueError("Empty test program")
    origin = program.origin
    if type(origin) is not int or not 0 <= origin < MEMORY_SIZE:
        raise ValueError("Program origin outside 6502 memory or not an integer")
    symbols = dict(program.symbols)
    _validate_symbols(symbols, program.exports)
    program_end = origin + len(program.code)
    if program_end > MEMORY_SIZE:
        raise ValueError("Test program does not fit in the allocated memory")
    for name in ("test_case", "final_result"):
        if origin <= symbols[name] < program_end:
            raise ValueError(f"Test program overlaps {name}")
    if symbols["test_case"] == symbols["final_result"]:
        raise ValueError("test_case and final_result overlap")
    if not origin <= symbols["end"] < program_end:
        raise ValueError("end is outside the test program")

    hw = py4hw.HWSystem()
    reset = hw.wire("reset")
    irq = hw.wire("irq")
    nmi = hw.wire("nmi")
    cpu_port = punxa.MemoryInterface(hw, "cpu_port", 8, 16)
    mem_port = punxa.MemoryInterface(hw, "mem_port", 8, 22)
    memory = punxa.SparseMemory(
        hw, "main_memory", 8, 32, mem_port, mem_base=0
    )
    punxa.MultiplexedBus(hw, "bus", cpu_port, [(mem_port, 0)])
    cpu = (adapter.create_cpu(hw, cpu_port, reset, irq, nmi, origin)
           if adapter else punxa.SingleCycle6502(
               hw, "cpu", cpu_port, reset, irq, nmi, origin))
    memory.reallocArea(0, MEMORY_SIZE, verbose=False)
    for offset, byte in enumerate(program.code):
        memory.writeByte(origin + offset, byte)
    memory.writeByte(symbols["test_case"], 0)
    memory.writeByte(symbols["final_result"], 0)
    return hw, cpu, memory, symbols


def prepare_test(binary=TEST_FILE, label_file=SYMBOL_FILE, *, adapter=None):
    """Compatibility loader for AssemblyResult or explicitly saved .bin/.lbl files.

    No external tools are called. Standard source-file execution uses
    prepare_program() directly and never requires these legacy files.
    """
    if isinstance(binary, AssemblyResult):
        return prepare_program(binary, adapter=adapter)
    symbols = read_symbols(label_file)
    program = AssemblyResult(PROGRAM_START, Path(binary).read_bytes(),
                             symbols, frozenset(symbols))
    return prepare_program(program, adapter=adapter)


@dataclass(frozen=True)
class TestResult:
    """A file outcome; protocol violations are ERROR, never PASS."""
    name: str
    category: str
    outcome: str
    case: int | None = None
    cycles: int = 0
    pc: int | None = None
    detail: str = ""
    retired: int | None = None

    @property
    def passed(self):
        return self.outcome == "PASS"


def test_category(source):
    """Match ATmega's test_<category> prefix without a fixed category list."""
    parts = Path(source).stem.split("_", 2)
    if len(parts) == 3 and parts[0].lower() == "test" and parts[1]:
        return "test_" + parts[1].lower()
    return "uncategorized"


def execute_test(hw, cpu, memory, symbols, name="test_data_LDA.asm",
                 max_cycles=None, *, adapter=None, observer=None):
    """Return a structured result at retirement; never stop on status alone."""
    if max_cycles is None:
        max_cycles = adapter.max_cycles if adapter else MAX_CYCLES
    if max_cycles <= 0:
        raise ValueError("max_cycles must be positive")
    cycles = 0
    retired = None

    def result(outcome, detail=""):
        try:
            pc = adapter.pc(cpu) if adapter else cpu.pc
        except Exception as exc:
            pc = None
            outcome = "ERROR"
            detail += f"; PC observation failed: {type(exc).__name__}: {exc}"
        return TestResult(name, test_category(name), outcome,
                          memory.readByte(symbols["test_case"]), cycles,
                          pc, detail,
                          retired if adapter else None)

    try:
        simulator = hw.getSimulator()
        retired = last_retired = cpu.getRetiredInstructions()
        for cycles in range(1, max_cycles + 1):
            if adapter:
                adapter.clock(simulator)
            else:
                simulator.clk(1)
            retired = cpu.getRetiredInstructions()
            if observer is not None:
                observer(cycles, cpu, memory)
            if retired == last_retired:
                continue
            last_retired = retired
            if (adapter.pc(cpu) if adapter else cpu.pc) != symbols["end"]:
                continue
            status = memory.readByte(symbols["final_result"])
            if status == 1:
                return result("PASS")
            if status == 255:
                return result("FAIL", "assembly assertion failed")
            return result("ERROR", f"PROTOCOL ERROR: final_result=0x{status:02X}")
    except Exception as exc:
        detail = (adapter.error_detail(exc) if adapter else
                  f"{type(exc).__name__}: {exc}")
        return result("ERROR", detail)
    return result("TIMEOUT", "end was not reached")


def format_result(result):
    fields = [f"case={result.case}", f"cycles={result.cycles}"]
    if result.retired is not None:
        fields.append(f"retired={result.retired}")
    if result.pc is not None:
        fields.append(f"PC=0x{result.pc:04X}")
    text = f"{result.outcome}: {result.name} ({', '.join(fields)})"
    if result.detail:
        text += " - " + result.detail.replace("\n", " | ")
    return text


def run_test(hw, cpu, memory, symbols, name="test_data_LDA.asm",
             max_cycles=None):
    """Keep the existing low-level boolean API and protocol-error diagnostic."""
    result = execute_test(hw, cpu, memory, symbols, name, max_cycles)
    text = format_result(result)
    if result.detail.startswith("PROTOCOL ERROR:"):
        text = text.replace("ERROR:", "PROTOCOL ERROR:", 1)
    # CPU output may end with an unfinished instruction trace.
    print("\n" + text)
    return result.passed


class _CPUTrace(io.TextIOBase):
    """Discard quiet traces without buffering an entire simulation in memory."""
    def __init__(self, stream=None):
        self.stream = stream
        self.at_line_start = True

    def write(self, text):
        if text:
            self.at_line_start = text.endswith("\n")
        if self.stream is not None:
            self.stream.write(text)
        return len(text)

    def flush(self):
        if self.stream is not None:
            self.stream.flush()


def build_test(source, build_dir=None, cc65_bin=None):
    """Return AssemblyResult using the Python assembler, without output files.

    Legacy build_dir and cc65_bin arguments are accepted but ignored. Callers
    that unpacked two output paths must instead consume the returned result.
    """
    source = Path(source).resolve()
    if source.suffix.lower() != ".asm" or not source.is_file():
        raise ValueError(f"Not an assembly test file: {source}")
    return assemble_file(source, origin=PROGRAM_START,
                         include_dirs=(TEST_DIR / "isa",))


def resolve_test(value, test_dir=None):
    path = Path(value)
    if path.is_file():
        return path.resolve()
    name = path.name if path.suffix else path.name + ".asm"
    directory = Path(test_dir) if test_dir is not None else TEST_DIR / "isa"
    candidate = directory / name
    if path.parent == Path(".") and candidate.is_file():
        return candidate.resolve()
    raise FileNotFoundError(f"Test not found: {value}")


def run_file_result(source, cc65_bin=None, max_cycles=None, trace=False,
                    test_dir=None, *, adapter=None):
    """Fresh build and hardware for every file; all failures become outcomes."""
    name = Path(source).name
    output = _CPUTrace(sys.stdout if trace else None)
    try:
        if max_cycles is None:
            max_cycles = adapter.max_cycles if adapter else MAX_CYCLES
        if max_cycles <= 0:
            raise ValueError("max_cycles must be positive")
        source = resolve_test(source, test_dir)
        name = source.name
        program = build_test(source, cc65_bin=cc65_bin)
        hardware = prepare_program(program, adapter=adapter)
        with redirect_stdout(output):
            result = execute_test(*hardware, name=name, max_cycles=max_cycles,
                                  adapter=adapter)
    except Exception as exc:
        result = TestResult(name, test_category(name), "ERROR",
                            detail=f"{type(exc).__name__}: {exc}")
    if trace and not output.at_line_start:
        print()
    return result


def run_file(source, cc65_bin=None, max_cycles=None, trace=False,
             test_dir=None, *, adapter=None):
    """Preserve the existing single-file boolean entry point."""
    result = run_file_result(source, cc65_bin, max_cycles, trace, test_dir,
                             adapter=adapter)
    print(format_result(result))
    return result.passed


def discover_tests(test_dir=None, categories=None):
    """Discover direct .asm children only, so results/fixtures are not ISA tests."""
    directory = Path(test_dir) if test_dir is not None else TEST_DIR / "isa"
    if not directory.is_dir():
        raise ValueError(f"Test directory not found: {directory}")
    tests = sorted(
        (p.resolve() for p in directory.iterdir()
         if p.is_file() and p.suffix.lower() == ".asm"),
        key=lambda p: (p.name.casefold(), p.name))
    if not tests:
        raise ValueError(f"No .asm tests found in {directory}")
    if isinstance(categories, str):
        categories = [categories]
    requested = set()
    for category in categories or ():
        category = category.strip().lower()
        if not category:
            raise ValueError("Category must not be empty")
        if category != "uncategorized" and not category.startswith("test_"):
            category = "test_" + category
        requested.add(category)
    available = {test_category(path) for path in tests}
    unknown = requested - available
    if unknown:
        raise ValueError("No tests for categories: " + ", ".join(sorted(unknown)))
    return [p for p in tests
            if not requested or test_category(p) in requested]


def computeAllTests(test_dir=None, categories=None, cc65_bin=None,
                    max_cycles=None, trace=False, *, adapter=None):
    """Corresponds to ATmega computeAllTests: run all selected files in order."""
    results = {}
    for source in discover_tests(test_dir, categories):
        result = run_file_result(source, cc65_bin, max_cycles, trace, adapter=adapter)
        results[source.name] = result
        print(format_result(result))
    return results


def summarize_results(results):
    """Count files, not assembly scenarios."""
    groups = {}
    for result in results.values():
        groups.setdefault(result.category, []).append(result)

    def counts(items):
        values = Counter(result.outcome for result in items)
        return {**{name: values[name] for name in ("PASS", "FAIL", "TIMEOUT", "ERROR")},
                "total": len(items),
                "pass_rate": 100 * values["PASS"] / len(items) if items else 0.0}

    return {"categories": {name: counts(groups[name]) for name in sorted(groups)},
            "total": counts(list(results.values()))}


def print_summary(results):
    summary = summarize_results(results)
    print("\nCategory             PASS FAIL TIMEOUT ERROR TOTAL   PASS%")
    for name, counts in [*summary["categories"].items(),
                         ("TOTAL", summary["total"])]:
        print(f"{name:20} {counts['PASS']:4} {counts['FAIL']:4} "
              f"{counts['TIMEOUT']:7} {counts['ERROR']:5} "
              f"{counts['total']:5} {counts['pass_rate']:6.1f}%")
    return summary


def runAllTests(test_dir=None, categories=None, cc65_bin=None,
                max_cycles=None, trace=False, *, adapter=None):
    """Corresponds to ATmega runAllTests; return results for automation."""
    results = computeAllTests(test_dir, categories, cc65_bin, max_cycles, trace,
                              adapter=adapter)
    print_summary(results)
    return results


def main(argv=None, *, adapter=None):
    parser = argparse.ArgumentParser(description=(adapter.description if adapter else __doc__))
    parser.add_argument("test", nargs="?", help="one test name or .asm path")
    parser.add_argument("--all", action="store_true", help="run all discovered tests")
    parser.add_argument("--category", action="append", default=[],
                        help="category, e.g. data or test_data; repeatable")
    parser.add_argument("--test-dir", type=Path,
                        help="discovery directory (default: isa/ beside this runner)")
    parser.add_argument("--list", action="store_true", help="list selected files only")
    parser.add_argument("--cc65-bin", type=Path,
                        help="deprecated compatibility option; ignored (uses Python assembler)")
    parser.add_argument("--max-cycles", type=int,
                        default=adapter.max_cycles if adapter else MAX_CYCLES)
    parser.add_argument("--trace", action="store_true")
    # Match the AVR batch spelling without eval or arbitrary command execution.
    parser.add_argument("-c", choices=["runAllTests()"], help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.cc65_bin is not None:
        print("warning: --cc65-bin is deprecated and ignored; tests use the Python assembler.",
              file=sys.stderr)
    if args.max_cycles <= 0:
        parser.error("--max-cycles must be positive")
    batch = args.all or bool(args.category) or args.c is not None
    if batch and args.test:
        parser.error("choose either one test or --all/--category/-c")
    try:
        if args.list:
            tests = ([resolve_test(args.test, args.test_dir)] if args.test else
                     discover_tests(args.test_dir, args.category))
            for source in tests:
                print(f"{test_category(source):20} {source.name}")
            return 0
        if batch:
            results = runAllTests(args.test_dir, args.category, args.cc65_bin,
                                  args.max_cycles, args.trace, adapter=adapter)
            return 0 if all(r.passed for r in results.values()) else 1
        return 0 if run_file(args.test or "test_data_LDA", args.cc65_bin,
                            args.max_cycles, args.trace, args.test_dir, adapter=adapter) else 1
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
