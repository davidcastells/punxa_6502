# 6502 ISA tests

Self-checking NMOS 6502 assembly tests using one shared Python framework for
SingleCycle6502 and MultiCycle6502. The methodology follows the ATmega ISA tests:
numbered assembly scenarios, fixed expectations, a common result protocol,
independent execution per file, and batch reporting.

SingleCycle has broad formal coverage. MultiCycle reuses the same build,
execution and reporting code through an adapter; CPU compatibility is limited.

## Requirements and installation

- Python **3.10+**; the recorded validation environment used Python 3.11.9.
- **py4hw>=2025.4**, declared in the repository's
  [pyproject.toml](../../pyproject.toml) and installed by pip with this project.
- **[cc65](https://cc65.github.io/)**, including `ca65` and `ld65`.
  Recorded validation used cc65 V2.19.

Run all commands below from the **repository root**, containing `pyproject.toml`.
Create a virtual environment:

```sh
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on Linux/macOS with a POSIX shell:

```sh
. .venv/bin/activate
```

Install the project and its declared Python dependencies into that environment:

```sh
python -m pip install -e .
```

If using an existing local py4hw checkout, install it into the same environment
with `python -m pip install -e "<path-to-py4hw-checkout>"`.
Recorded runs used an editable py4hw checkout; a fresh package-only installation
has not been independently validated.

Follow the [cc65 setup guide](https://cc65.github.io/getting-started.html) and add
its executable directory to `PATH`, or append `--cc65-bin "<path-to-cc65-bin>"`
to any run command. This directory must contain both `ca65` and `ld65` (`.exe`
on Windows). Replace placeholders with your paths; assembly/linking is automatic.

## Quick start

List the formal tests without building or executing them:

```sh
python test/isa_tests/tb_ISA_tests.py --list
```

Run one SingleCycle test (the recorded LDX baseline is PASS):

```sh
python test/isa_tests/tb_ISA_tests.py test_data_LDX
```

Run the complete SingleCycle suite:

```sh
python test/isa_tests/tb_ISA_tests.py --all
```

Run the validated shared LDA-immediate test on MultiCycle:

```sh
python test/isa_tests/tb_ISA_tests_Multicycle.py test_data_LDA_Immediate
```

For a model comparison, select this same file with the SingleCycle entry point.
Its five cases verify A and Z for `$00/$3C/$80/$FF/$A5`; recorded results are
PASS on SingleCycle (481 clocks) and MultiCycle (974 clocks, 55 retired).
This subset does not establish full LDA, N or preserved-flag correctness.

## Selection, diagnostics and results

Both entry points accept the same options:

| Argument | Purpose |
| --- | --- |
| `test_data_LDX` | One test by stem, filename, or existing `.asm` path |
| `--list` | List the selected tests without assembly or CPU execution |
| `--all` | Discover and run every direct `.asm` child in `isa/` |
| `--category data` | Run a category; repeat for multiple categories |
| `--test-dir "<directory>"` | Override the test discovery directory |
| `--cc65-bin "<directory>"` | Locate the assembler and linker |
| `--trace` | Print CPU execution traces |
| `--max-cycles 20000` | Override the positive simulation-clock limit |
| `--help` | Show CLI usage |

Use `--list --category data` to inspect a category. Select either one file or
batch execution; each file gets a fresh build, CPU and 64 KiB memory environment.
A file failure, timeout or error does not prevent later batch files from running.
The summary counts files by category and overall, not individual assembly cases.

Completion requires an instruction retirement at exported `end`. The runner
reads linked `test_case` and `final_result` symbols: 1 means PASS, 255 means FAIL,
and every other result value is a protocol ERROR. Build/runtime errors are ERROR;
failure to reach completion within the clock limit is TIMEOUT.
Defaults: SingleCycle **10000** clocks; MultiCycle **100000** (provisional).
These are simulation clocks, not physical NMOS instruction-cycle measurements.
Execution exits 0 only when every selected file passes; any non-PASS exits 1.
Listing exits 0; invalid CLI arguments or selections exit 2.

## Current verified SingleCycle baseline

As of 2026-10-27: **36 formal files; 29 PASS / 7 FAIL / 0 TIMEOUT / 0 ERROR**.
The full `--all` command therefore currently exits **1**. The seven known failures:

| File | First failing case | Known behavior |
| --- | --- | --- |
| `test_data_LDA.asm` | 30 | Zero-page indirect pointer wrapping |
| `test_arith_INX.asm` | 5 | Incorrect Z update |
| `test_arith_INC.asm` | 5 | Flags at the FF-to-00 boundary |
| `test_bitmap_ASL.asm` | 4 | Result width / memory write-back defects |
| `test_data_PLA.asm` | 1 | Missing N/Z updates |
| `test_logic_ORA.asm` | 13 | Shared zero-page indirect pointer wrapping |
| `test_arith_INY.asm` | 2 | Incorrect Z update; isolated case 6 also shows missing 8-bit Y wrapping |

Files stop at their first failed assertion; later cases are not implied to pass.
Formal targets cover **35/39 Execute-path mnemonics** and **107/116 opcode/mode
pairs**, including retained isolated-case observations; sequential execution
reaches **103/116** pairs. Coverage includes failing checks and does not mean correctness.
See [BATCH6_SUMMARY.md](BATCH6_SUMMARY.md) for INY/DEY/DEC scenarios and findings.
DEC's eight scenarios PASS; its raw internal N=-1 observation is recorded separately.

## MultiCycle compatibility and scope

The shared LDA-immediate A/Z subset above is the validated MultiCycle entry point.
Most other files are blocked by missing helpers (including CLD/PHP), missing
target opcodes/modes, and incomplete flag/address/stack behavior. Encountering
an unsupported opcode reports ERROR with `UNSUPPORTED_CPU` detail; a compatibility
record marked NOT_RUN means the file was not executed, not that it passed.

Expectations remain NMOS 6502 semantics. Current broader flag tests use the
simulator's initial I=0 convention; they do not verify physical reset or I=1.
Decimal arithmetic, exhaustive inputs, physical timing and IRQ/NMI are outside
the current verified scope. PHP live N/V/D/I preservation additionally has
read-only observation evidence beyond the assembly file's own assertions.

See [COVERAGE.md](COVERAGE.md) for instruction/mode coverage and known defects,
and [MULTICYCLE_COMPATIBILITY.md](MULTICYCLE_COMPATIBILITY.md) for the initial
MultiCycle file/dependency assessment and CPU limitations.
