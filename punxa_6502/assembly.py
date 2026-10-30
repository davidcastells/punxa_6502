"""In-process NMOS 6502 assembler for the formal ISA tests' ca65 subset.

The frontend expands once, then layout fixes every instruction's width before
emission resolves forward references. No external assembler, linker or CPU is
used. CODE defaults to $0200 and may never enter the data area at $1000.

This is not a general ca65 replacement: there is one CODE segment and no
address-size overrides/relaxation. Known integer operands use zero page when
legal; unresolved operands conservatively reserve an absolute form when one
exists. Equates are immutable, symbols case-sensitive. Alignment is relative
to the CODE segment, as in ca65, rather than to a guessed absolute address.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from . import instruction_decode as isa
from .asm_expressions import ExpressionError, UndefinedSymbolError, evaluate
from .asm_frontend import AssemblyError, SourceLine, _split_arguments, preprocess


__all__ = ["AssemblyError", "AssemblyResult", "ListingEntry",
           "assemble_file", "assemble_program"]

_IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
_LABEL = re.compile(rf"^({_IDENTIFIER}):$")
_ASSIGNMENT = re.compile(rf"^({_IDENTIFIER})\s*=\s*(.+)$")
_DIRECTIVE = re.compile(r"^(\.[A-Za-z_][A-Za-z_0-9]*)\b(.*)$")
_DATA_START = 0x1000

# Reuse instruction metadata, never CPU Execute behavior, for the legal catalog.
# Required encodings are independently checked with literal test vectors.
_ENCODINGS: dict[tuple[str, str], int] = {}
for _opcode, _definition in enumerate(isa._OPCODE_MAP):
    if _definition is not None:
        if _definition in _ENCODINGS:
            raise RuntimeError(f"ambiguous opcode metadata: {_definition}")
        _ENCODINGS[_definition] = _opcode
_MNEMONICS = {mnemonic for mnemonic, mode in _ENCODINGS}


@dataclass(frozen=True)
class ListingEntry:
    """An instruction or data/padding directive and its source location.

    Directive entries use their uppercase name as mnemonic and DATA/FILL as
    mode. Raw .byte/.word instructions remain data; no disassembly is inferred.
    """

    address: int
    data: bytes
    mnemonic: str
    mode: str
    source: SourceLine


@dataclass(frozen=True)
class AssemblyResult:
    origin: int
    code: bytes
    symbols: dict[str, int]
    exports: frozenset[str]
    listing: tuple[ListingEntry, ...] = ()


@dataclass(frozen=True)
class _Instruction:
    address: int
    mnemonic: str
    mode: str
    expression: str | None
    source: SourceLine


@dataclass(frozen=True)
class _Data:
    address: int
    directive: str
    expressions: tuple[str, ...]
    width: int
    source: SourceLine


@dataclass(frozen=True)
class _Fill:
    address: int
    directive: str
    count: int
    value: int
    source: SourceLine


def _value(expression: str, symbols: dict[str, int], pc: int,
           source: SourceLine) -> int:
    try:
        return evaluate(expression, symbols, pc=pc)
    except ExpressionError as error:
        raise AssemblyError(str(error), source) from error


def _instruction(text: str, symbols: dict[str, int], pc: int,
                 source: SourceLine) -> _Instruction:
    parts = text.split(None, 1)
    mnemonic = parts[0].upper()
    if mnemonic not in _MNEMONICS:
        raise AssemblyError(f"unknown instruction: {parts[0]}", source)
    operand = parts[1].strip() if len(parts) > 1 else ""
    expression = None
    if not operand:
        mode = isa.ADDRESSING_IMPLIED
        if (mnemonic, mode) not in _ENCODINGS:
            mode = isa.ADDRESSING_ACCUMULATOR
    elif operand.lower() == "a" and (mnemonic, isa.ADDRESSING_ACCUMULATOR) in _ENCODINGS:
        mode = isa.ADDRESSING_ACCUMULATOR
    elif (mnemonic, isa.ADDRESSING_RELATIVE) in _ENCODINGS:
        mode, expression = isa.ADDRESSING_RELATIVE, operand
    elif operand.startswith("#"):
        mode, expression = isa.ADDRESSING_IMMEDIATE, operand[1:].strip()
    else:
        indexed_indirect = re.fullmatch(r"\((.+),\s*[xX]\s*\)", operand)
        indirect_indexed = re.fullmatch(r"\((.+)\)\s*,\s*[yY]", operand)
        indirect = re.fullmatch(r"\((.+)\)", operand)
        if indexed_indirect:
            mode, expression = isa.ADDRESSING_INDIRECTX, indexed_indirect[1].strip()
        elif indirect_indexed:
            mode, expression = isa.ADDRESSING_INDIRECTY, indirect_indexed[1].strip()
        elif indirect:
            mode, expression = isa.ADDRESSING_INDIRECT, indirect[1].strip()
        else:
            if operand.startswith("("):
                raise AssemblyError("unsupported indirect operand; expected (expr,x), (expr),y or (expr)", source)
            indexed = re.fullmatch(r"(.+),\s*([xXyY])", operand)
            expression = indexed[1].strip() if indexed else operand
            index = indexed[2].upper() if indexed else ""
            small, large = {
                "": (isa.ADDRESSING_ZEROPAGE, isa.ADDRESSING_ABSOLUTE),
                "X": (isa.ADDRESSING_ZEROPAGEX, isa.ADDRESSING_ABSOLUTEX),
                "Y": (isa.ADDRESSING_ZEROPAGEY, isa.ADDRESSING_ABSOLUTEY),
            }[index]
            try:
                known = evaluate(expression, symbols, pc=pc)
            except UndefinedSymbolError:
                known = None
            except ExpressionError as error:
                raise AssemblyError(str(error), source) from error
            # Width is selected once. Never guess that an unresolved label is 0.
            if ((mnemonic, small) in _ENCODINGS
                    and (known is not None and 0 <= known <= 255
                         or (mnemonic, large) not in _ENCODINGS)):
                mode = small
            else:
                mode = large
    if (mnemonic, mode) not in _ENCODINGS:
        raise AssemblyError(f"unsupported addressing mode {mode} for {mnemonic}: {operand}", source)
    return _Instruction(pc, mnemonic, mode, expression, source)


def _encode(instruction: _Instruction, symbols: dict[str, int]) -> bytes:
    size = isa.OPERAND_SIZE_MAP[instruction.mode]
    data = bytes([_ENCODINGS[instruction.mnemonic, instruction.mode]])
    if not size:
        return data
    value = _value(instruction.expression, symbols, instruction.address, instruction.source)
    if instruction.mode == isa.ADDRESSING_RELATIVE:
        if not 0 <= value <= 0xFFFF:
            raise AssemblyError(f"branch target outside 16-bit address space: {value}", instruction.source)
        displacement = value - (instruction.address + 2)
        if not -128 <= displacement <= 127:
            raise AssemblyError(f"branch displacement {displacement} outside -128..127", instruction.source)
        return data + bytes([displacement & 255])
    maximum = (1 << (size * 8)) - 1
    if not 0 <= value <= maximum:
        raise AssemblyError(f"operand {value} outside 0..{maximum} for {instruction.mode}", instruction.source)
    return data + value.to_bytes(size, "little")


def _listing_entry(record: _Instruction | _Data | _Fill,
                   symbols: dict[str, int]) -> ListingEntry:
    if isinstance(record, _Instruction):
        return ListingEntry(record.address, _encode(record, symbols),
                            record.mnemonic, record.mode, record.source)
    if isinstance(record, _Fill):
        data = bytes([record.value]) * record.count
        mode = "FILL"
    else:
        values = bytearray()
        for expression in record.expressions:
            value = _value(expression, symbols, record.address + len(values), record.source)
            maximum = (1 << (8 * record.width)) - 1
            if not 0 <= value <= maximum:
                raise AssemblyError(f"{record.directive} value {value} outside 0..{maximum}", record.source)
            values.extend(value.to_bytes(record.width, "little"))
        data, mode = bytes(values), "DATA"
    return ListingEntry(record.address, data, record.directive.upper(), mode, record.source)


def assemble_program(
    source: str,
    origin: int = 0x0200,
    max_size: int = 0x0E00,
    include_dirs: Sequence[str | Path] = (),
    *,
    source_name: str = "<string>",
) -> AssemblyResult:
    """Assemble source into bytes/symbols without creating any output files.

    Includes resolve relative to ``source_name``, then ``include_dirs``.
    Includes/macros/conditionals/repeats are expanded before layout. Data and
    padding directives are .byte, .word, .res and .align (default fill zero).
    Counts/alignment/fills must be known at their declaration; data values may
    reference forward labels. Unknown directives are errors. ``error`` assertions
    are checked as soon as resolvable within assembly; ``lderror`` assertions
    are checked against the final linked layout after assembly assertions.
    """
    if not isinstance(origin, int) or not 0 <= origin < _DATA_START:
        raise AssemblyError("CODE origin must be an integer below reserved data at $1000")
    if not isinstance(max_size, int) or max_size < 0:
        raise AssemblyError("max_size must be a nonnegative integer")
    lines = preprocess(source, filename=str(source_name), include_dirs=include_dirs)
    symbols: dict[str, int] = {}
    definitions: set[str] = set()
    exports: dict[str, SourceLine] = {}
    pending: list[tuple[str, str, int, SourceLine]] = []
    assertions: list[tuple[str, str, str, int, SourceLine]] = []
    records: list[_Instruction | _Data | _Fill] = []
    pc = origin

    def reserve(record: _Instruction | _Data | _Fill, count: int):
        nonlocal pc
        pc += count
        if pc - origin > max_size:
            raise AssemblyError(f"CODE exceeds max_size ${max_size:04X}", record.source)
        if pc > _DATA_START:
            raise AssemblyError("CODE overlaps reserved data beginning at $1000", record.source)
        records.append(record)

    # Pass 1: assign byte addresses and freeze every instruction's mode/width.
    for line in lines:
        text = line.text
        label = _LABEL.fullmatch(text)
        assignment = _ASSIGNMENT.fullmatch(text)
        if label or assignment:
            name = (label or assignment)[1]
            if name in definitions:
                raise AssemblyError(f"duplicate symbol: {name}", line)
            definitions.add(name)
            if label:
                symbols[name] = pc
            else:
                expression = assignment[2]
                try:
                    symbols[name] = evaluate(expression, symbols, pc=pc)
                except UndefinedSymbolError:
                    pending.append((name, expression, pc, line))
                except ExpressionError as error:
                    raise AssemblyError(str(error), line) from error
            continue
        directive = _DIRECTIVE.fullmatch(text)
        if directive:
            name, argument = directive[1].lower(), directive[2].strip()
            if name in (".setcpu", ".segment"):
                expected = '"6502"' if name == ".setcpu" else '"CODE"'
                if argument != expected:
                    raise AssemblyError(f"only {name} {expected} is supported", line)
            elif name == ".export":
                names = [part.strip() for part in argument.split(",")]
                if any(not re.fullmatch(_IDENTIFIER, item) for item in names):
                    raise AssemblyError(".export requires comma-separated symbol names", line)
                for item in names:
                    exports[item] = line
            elif name == ".assert":
                match = re.fullmatch(r'(.+),\s*(error|lderror)\s*,\s*"([^"\n]*)"', argument)
                if not match:
                    raise AssemblyError('.assert requires expression, error/lderror, "message"', line)
                expression, phase, message = match[1].strip(), match[2], match[3]
                if phase == "error":
                    try:
                        condition = evaluate(expression, symbols, pc=pc)
                    except UndefinedSymbolError:
                        pass  # Forward references are resolved within this CODE unit.
                    except ExpressionError as error:
                        raise AssemblyError(str(error), line) from error
                    else:
                        if not condition:
                            raise AssemblyError(f"assembly assertion failed: {message}", line)
                        continue
                assertions.append((expression, phase, message, pc, line))
            elif name in (".byte", ".word"):
                expressions = tuple(_split_arguments(argument, line))
                if not expressions:
                    raise AssemblyError(f"{name} requires at least one expression", line)
                width = 1 if name == ".byte" else 2
                reserve(_Data(pc, name, expressions, width, line), width * len(expressions))
            elif name in (".res", ".align"):
                arguments = _split_arguments(argument, line)
                if not 1 <= len(arguments) <= 2:
                    raise AssemblyError(f"{name} requires count/alignment and optional fill byte", line)
                amount = _value(arguments[0], symbols, pc, line)
                fill = _value(arguments[1], symbols, pc, line) if len(arguments) == 2 else 0
                if not 0 <= fill <= 255:
                    raise AssemblyError(f"{name} fill byte outside 0..255: {fill}", line)
                if name == ".align":
                    if not 1 <= amount <= 65536:
                        raise AssemblyError(".align requires an alignment in 1..65536", line)
                    count = (-(pc - origin)) % amount
                else:
                    if amount < 0:
                        raise AssemblyError(".res count must be nonnegative", line)
                    count = amount
                reserve(_Fill(pc, name, count, fill, line), count)
            else:
                raise AssemblyError(f"unsupported directive: {name}", line)
            continue
        instruction = _instruction(text, symbols, pc, line)
        reserve(instruction, 1 + isa.OPERAND_SIZE_MAP[instruction.mode])

    # Immutable forward equates are resolved without revisiting frozen layout.
    while pending:
        unresolved = []
        for name, expression, location, line in pending:
            try:
                symbols[name] = evaluate(expression, symbols, pc=location)
            except UndefinedSymbolError:
                unresolved.append((name, expression, location, line))
            except ExpressionError as error:
                raise AssemblyError(str(error), line) from error
        if len(unresolved) == len(pending):
            name, expression, location, line = unresolved[0]
            raise AssemblyError(f"undefined or cyclic equate {name}: {expression}", line)
        pending = unresolved

    def check_assertions(phase: str):
        for expression, requested_phase, message, location, line in assertions:
            if requested_phase == phase and not _value(expression, symbols, location, line):
                stage = "assembly" if phase == "error" else "link"
                raise AssemblyError(f"{stage} assertion failed: {message}", line)

    # Finish assembly (including all operand resolution) before link assertions.
    check_assertions("error")
    for name, line in exports.items():
        if name not in symbols:
            raise AssemblyError(f"exported symbol is undefined: {name}", line)
    # Pass 2: emit using resolved symbols, never resize an instruction or block.
    listing = tuple(_listing_entry(item, symbols) for item in records)
    check_assertions("lderror")
    return AssemblyResult(origin, b"".join(item.data for item in listing),
                          symbols, frozenset(exports), listing)


def assemble_file(
    path: str | Path,
    origin: int = 0x0200,
    max_size: int = 0x0E00,
    include_dirs: Sequence[str | Path] = (),
) -> AssemblyResult:
    """Read a UTF-8 source file and return its in-memory assembly result."""
    path = Path(path).resolve()
    try:
        source = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise AssemblyError(f"cannot read source {path}: {error}") from error
    return assemble_program(source, origin, max_size, include_dirs,
                            source_name=str(path))
