# Python 6502 Assembler: Design and Verification

This document describes the implementation after Phases 1 and 2, inspected on
28 October 2026 on `feature/6502-python-assembler`. It explains the current code,
its verified assembly output, and its boundaries. Phase 3 integration with the
ISA runner has **not** been implemented.

Source paths below are relative to the `punxa_6502` repository unless explicitly
identified as part of the adjacent ATmega checkout. Hexadecimal addresses use
6502 notation (`$0200`); hexadecimal machine-code bytes are written as `A9 01`.

## 1. Purpose and relationship to the ISA framework

The assembler converts self-checking assembly tests into machine-code bytes and
symbols inside the Python process. The tests continue to define their own
expected register, memory and flag values. The assembler encodes those tests;
it neither executes instructions nor decides whether a CPU implements them
correctly.

An in-process assembler fits the framework because the Python testbench needs
two products: a program image to load into simulated memory and symbol addresses
such as `test_case`, `final_result` and `end`. Returning these products directly
can remove executable discovery, subprocess invocation and intermediate-file
parsing from the eventual test execution workflow. Source locations and macro
expansion traces also make assembly errors accessible to the Python caller.

The current and prospective workflows must be distinguished:

| Aspect | Current ISA runner | Implemented Python assembler |
| --- | --- | --- |
| Entry point | `tb_ISA_tests.py::build_test()` | `assemble_file()` or `assemble_program()` |
| Assembly | External `ca65`, producing an object file | Python frontend, layout and byte emission |
| Placement | External `ld65` with `isa_test.cfg` | One CODE segment with origin and size arguments |
| Products | `.bin` and VICE `.lbl` files, consumed by `prepare_test()` | `AssemblyResult` containing bytes and symbols |
| Integration status | Still used for CPU test execution | Independently validated; not yet connected to the runner |

The existing [runner][runner] still invokes ca65/ld65. Nothing in the new
assembler silently falls back to those tools. The development comparison scripts
invoke them separately as a reference.

### What was borrowed from ATmega

The architectural reference is the adjacent checkout's
`punxa_atmega328p/punxa_atmega328p/assembly.py`, especially
`assemble_program()`, `parts_to_ins()` and its two assembly passes. Its runner,
`punxa_atmega328p/test/isa_tests/tb_ISA_tests.py`, calls the assembler from
`prepareTest()`, loads returned words, and uses returned symbols in `runTest()`.

The reusable ideas are the source-to-code-and-symbols API, label collection
before final operand resolution, and symbol-driven test completion. The 6502
implementation supplies different encoding and preprocessing algorithms:

| Reference behavior | 6502 adaptation |
| --- | --- |
| AVR instructions returned as 16-bit words | NMOS 6502 instructions returned as bytes, with lengths of 1–3 bytes |
| Word-addressed labels and relative offsets from `word_PC + 1` | Byte-addressed labels and branch offsets from `byte_PC + 2` |
| Hand-written instruction encoder in `parts_to_ins()` | Reverse lookup of existing mnemonic/addressing-mode metadata |
| Pass 1 temporarily replaces label operands with zero to count words | Pass 1 freezes a legal addressing mode and never guesses an unresolved label is zero |
| `expand_macros()` handles textual `high()`/`low()` substitutions | Real parameterized/nested macro expansion, includes and local labels |
| Some unrecognized directives are skipped | Unsupported active syntax produces explicit errors |

The ATmega assembler is not the source of the implemented `.macro`, `.include`,
conditional or repetition facilities. Those were developed for the 6502 corpus.

## 2. Modules and processing pipeline

| Module | Main responsibilities and functions |
| --- | --- |
| [assembly.py][assembly] | Public API; `_ENCODINGS`; `_instruction()`; layout in `assemble_program()`; `_encode()`; `_listing_entry()`; exports and assertions |
| [asm_frontend.py][frontend] | `preprocess()`; source records; `_Preprocessor.include()`, `expand()`, `_process()` and `repeat_lines()`; comments and argument splitting |
| [asm_expressions.py][expressions] | `_tokenize()`; precedence parser `_Parser`; safe integer evaluation through `evaluate()` |
| [instruction_decode.py][opcodes] | Existing `_OPCODE_MAP`, addressing-mode constants and `OPERAND_SIZE_MAP`; metadata used by the assembler |

The actual pipeline is:

```text
assemble_file(path)                         assemble_program(source)
        | UTF-8-sig read, resolved filename          |
        +-------------------------+-----------------+
                                  |
                    validate origin and max_size
                                  |
                       frontend.preprocess()
              comments -> includes/guards -> macros
                     -> conditionals/repeats
                                  |
                  ordered list of SourceLine records
                                  |
                     Pass 1: layout and symbols
            labels/equates, frozen instruction modes,
            fixed data widths, alignment/padding counts
                                  |
             resolve pending equates; deferred error checks;
                       validate exported names
                                  |
                         Pass 2: emission
           resolve operands/data, check ranges, encode bytes
                                  |
                  check final lderror assertions
                                  |
                         AssemblyResult
              origin + code + symbols + exports + listing
                                  |
           [future Phase 3: adapt runner loading/validation]
                                  |
                    SingleCycle / MultiCycle execution
```

Preprocessing runs once. The two passes operate on the same expanded source;
they do not expand macros again and risk generating different local labels.
Pending-equate resolution is an additional symbol-resolution loop between
layout and emission, not an instruction-size relaxation pass.

## 3. Public API and returned data

[assembly.py][assembly] exposes:

```python
assemble_file(path, origin=0x0200, max_size=0x0E00, include_dirs=())
assemble_program(source, origin=0x0200, max_size=0x0E00,
                 include_dirs=(), *, source_name="<string>")
```

`assemble_file()` resolves the input path, reads UTF-8 with optional BOM, and
delegates to `assemble_program()`. `source_name` gives in-memory source a filename
for diagnostics and relative include lookup. The API itself writes no object,
binary or label files.

Both return `AssemblyResult`:

| Field | Type and meaning |
| --- | --- |
| `origin` | Integer byte address where the returned image starts |
| `code` | Contiguous `bytes`, including explicitly emitted data and padding |
| `symbols` | Dictionary of resolved labels and equates, including internal macro labels |
| `exports` | `frozenset` of explicitly exported names; addresses are obtained from `symbols` |
| `listing` | Tuple of `ListingEntry` records containing address, bytes, mnemonic, mode and original `SourceLine` |

Instruction listing entries use modes such as `IMM` or `ABS`. Data directives
use their uppercase names, for example `.WORD`, with mode `DATA`; padding uses
mode `FILL`. Raw opcode bytes are preserved as data rather than disassembled.
`AssemblyResult` is a frozen dataclass, but its `symbols` dictionary is mutable;
callers should treat the returned mapping as assembly output.

For example, from the repository root:

```python
from punxa_6502.assembly import assemble_file

result = assemble_file("test/isa_tests/isa/test_arith_ADC.asm")
assert result.origin == 0x0200
assert result.symbols["end"] == 0x04A5
exported_symbols = {name: result.symbols[name] for name in result.exports}
print(result.code[:9].hex(" "))  # a2 ff 9a d8 a9 00 8d 04 20
```

The assembler is generic within its supported language: it does not require
protocol symbols or validate that `end` lies inside the image. The current
runner's `read_symbols()` and `prepare_test()` perform those protocol checks.
Phase 3 must retain them when receiving symbols directly.

The assembler modules introduce no external assembler dependency. Normal
`punxa_6502.assembly` import nevertheless executes the package's existing
`__init__.py`, which imports hardware modules using the project's existing
`py4hw` dependency. Assembly does not instantiate or clock a CPU; it is not a
separately packaged, dependency-free command-line assembler.

## 4. Instruction parsing, opcode lookup and encoding

### 4.1 From metadata to an encoding table

At import time, [assembly.py][assembly] iterates over
`instruction_decode._OPCODE_MAP`. That existing table maps each populated opcode
to `(mnemonic, mode)`. The assembler reverses it into:

```text
_ENCODINGS[("ADC", "IMM")] = $69
_ENCODINGS[("ADC", "Z")]   = $65
_ENCODINGS[("ADC", "ABS")] = $6D
```

A duplicate mnemonic/mode pair raises `RuntimeError` instead of selecting an
ambiguous opcode. The catalog currently contains 151 forms across 56 mnemonics
and 13 addressing classes. These are encoding definitions, not evidence that
either CPU executes every entry correctly. Fixed encoding vectors and the
independent ca65/ld65 comparisons validate the forms used by the test corpus.

### 4.2 Operand syntax determines the candidate mode

`_instruction()` splits a source line into mnemonic and optional operand. It
uppercases the mnemonic, checks `_MNEMONICS`, then recognizes operand shapes:

| Source shape | Mode(s) selected or considered | Operand bytes |
| --- | --- | --- |
| No operand, e.g. `clc` | `IMP`; otherwise `A` if that form exists | 0 |
| `ror a` | `A` | 0 |
| `adc #expr` | `IMM` | 1 |
| Branch mnemonic and target expression | `R` | 1 signed displacement |
| `adc expr` | `Z` or `ABS` | 1 or 2 |
| `adc expr,x` | `ZX` or `ABSX` | 1 or 2 |
| `lda expr,y` | `ZY` or `ABSY`, according to legal availability | 1 or 2 |
| `adc (expr,x)` | `INDX` | 1 |
| `adc (expr),y` | `INDY` | 1 |
| `jmp (expr)` | `IND` | 2 |

`OPERAND_SIZE_MAP[mode]` supplies operand length; total instruction length is
`1 + operand_length`. Mnemonics and index-register spelling are case-insensitive;
symbol and macro names are case-sensitive.

For direct or indexed operands, the parser considers both value and available
opcodes. If the expression is already known to be in `0..255`, it uses the
zero-page form when legal. Otherwise it reserves an absolute form when one
exists. If only the small form exists, emission later enforces its byte range.
The number of hexadecimal digits is irrelevant:

| Source | Bytes | Reason |
| --- | --- | --- |
| `lda $0040` | `A5 40` | Value is 64 and LDA has a zero-page form |
| `lda $40,y` | `B9 40 00` | LDA has no zero-page,Y form |
| `ldx $40,y` | `B6 40` | LDX has a zero-page,Y form |
| `jmp $40` | `4C 40 00` | JMP has no zero-page form |

An unsupported mnemonic/mode combination, such as `sta #1`, raises
`AssemblyError`. Unsupported indirect syntax is rejected explicitly rather
than reinterpreted as another mode.

### 4.3 Emitting operands

`_encode()` emits the opcode and evaluates the stored operand expression using
the resolved symbols. Byte operands must be in `0..255`; word operands must be
in `0..65535`. Values are not silently truncated. Explicit `<`/`>` extraction
can deliberately select one byte of a larger expression.

Word operands use `value.to_bytes(2, "little")`: the low byte comes first because
that is the NMOS 6502 instruction format. Thus `adc $1000` becomes `6D 00 10`.
The Python host's byte order does not affect this conversion.

Indexing and pointer reads occur at CPU execution time. For example,
`adc ($60,x)` encodes `61 60`, not a resolved effective address. Similarly,
`jmp ($12FF)` encodes `6C FF 12`; the NMOS indirect-JMP page-boundary behavior is
a CPU responsibility. The assembler does not emulate or repair it.

### 4.4 Relative branches

For a branch at byte address `P` targeting `T`, `_encode()` computes:

```text
displacement = T - (P + 2)
accepted range = -128 through +127
encoded operand = displacement & $FF
```

The `+2` accounts for the opcode and operand bytes. In the ADC image, a BEQ at
`$0220` targets `$0225`: `$0225 - $0222 = 3`, producing `F0 03`.
For a backward example, `bne start` at `$0204` with `start=$0200` gives
`$0200 - $0206 = -6`, encoded as `D0 FA`. Out-of-range branches fail; no long
branch or replacement JMP is inserted.

## 5. Frontend: includes, macros and expansion

### 5.1 Source records and include lookup

`preprocess()` creates a new `_Preprocessor` for each assembly call.
`_Preprocessor.lines()` creates `SourceLine(text, filename, line, expansion)`
records. `_without_comment()` strips semicolon comments while respecting quoted
strings and escapes. Removing a comment does not change the physical line
number recorded for later diagnostics.

`_Preprocessor.include()` searches the including file's directory first, then
the supplied `include_dirs` in order. For the default `<string>` source name,
the initial directory is the current working directory. Included files are
read as UTF-8-sig and share the current assembly's macro/constant environment.
Missing files or malformed include arguments produce source-aware errors.

`.ifndef NAME` checks the set of names encountered so far, rather than evaluating
a numeric expression. In [test_protocol.inc][protocol], the first inclusion
defines `TEST_PROTOCOL_INCLUDED`; a subsequent inclusion skips its definitions.
There is a nesting limit of 64 includes, not a separate graph-based cycle
detector. A guarded recursive inclusion can terminate through the guard.

### 5.2 Macro parameters, nested calls and local labels

`_process()` stores `.macro` bodies as `_Macro` records without emitting them.
`expand()` checks the argument count, binds parameters to argument text and
recursively processes the substituted body. `_split_arguments()` separates
commas outside parentheses and quoted strings, so an argument containing a
parenthesized expression is not split incorrectly.

`_substitute()` replaces complete identifier tokens, preserving numeric literals
and quoted strings. It does not replace substrings inside other identifiers.
This is textual parameter substitution, not a general expression-tree macro
system or implicit insertion of parentheses.

Before expansion, `expand()` scans `.local` declarations. Every macro invocation
gets a new serial number; its local names become identifiers such as
`__asm_local_3_ok`. Nested invocations receive their own serials. Reusing an
ordinary `ok:` label across checks would otherwise cause duplicate definitions
or branches into another check. The generated names isolate those labels.

The ADC test contains:

```asm
.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro
```

During case 1, `CHECK_A $00` inside `CHECK_ADC` actually expands to:

```asm
    cmp #$00
    beq __asm_local_3_ok
    jmp fail
__asm_local_3_ok:
```

The next check uses `__asm_local_4_ok`. These exact names are observed for the
unchanged full ADC file; callers should not depend on their serial numbers as
an API. Changing preceding macro calls can change the numbers.

Source records retain macro definition locations and append invocation frames.
For example, the comparison still points to the `cmp #expected` definition,
with both the `CHECK_ADC` and nested `CHECK_A` call sites in its expansion trace.
`SourceLine.describe()` and `AssemblyError` expose that context to the caller.

### 5.3 Conditional and repeated source

`.if expression`, `.else` and `.endif` use `_Conditional` frames recording the
parent's active state, the selected condition and whether an else was seen.
Inactive nested conditions are not evaluated. Duplicate else clauses, unmatched
terminators and unterminated blocks fail explicitly.

Active conditions and repeat counts must be available during preprocessing.
Macro parameters have already been substituted; previously resolved constant
assignments are held in a separate frontend dictionary. Labels, current-PC
values and unresolved forward equates are not available to these controls.
The original assignment lines still reach the assembler for final evaluation.

The actual JMP test contains:

```asm
.repeat 7, index
    sta done_cases+index
.endrepeat
```

`_process()` collects the balanced body, evaluates the count and calls
`repeat_lines()` for each iteration. This emits `sta done_cases+0` through
`sta done_cases+6`. The optional iterator is substituted lexically, not added to
the exported or global symbol dictionary. Nested repeats and iterator shadowing
are implemented; repeated macro invocations still obtain fresh macro locals.
Count zero emits no body, and its contained expressions are not evaluated.

Repeat counts are limited to `0..65536`; macro-call depth to 64; total recursive
preprocessing depth to 128. Includes, macro bodies and repeat bodies must each
balance their own conditional blocks. Nested macro definitions are unsupported,
although nested macro invocations are supported.

### 5.4 Directives handled after preprocessing

The frontend passes the following directives to `assemble_program()`:

| Directive | Implemented effect |
| --- | --- |
| `.setcpu "6502"` | Validates the sole supported CPU selection; emits nothing |
| `.segment "CODE"` | Validates the sole supported segment; emits nothing |
| `name = expression` | Defines an immutable equate; allocates no bytes |
| `.export a, b` | Records names that must resolve before return |
| `.byte expr, ...` | Reserves one byte per expression; values may reference forward labels |
| `.word expr, ...` | Reserves two little-endian bytes per expression |
| `.res count[, fill]` | Emits `count` copies of a byte; default fill is zero |
| `.align alignment[, fill]` | Pads relative to the CODE segment; default fill is zero |
| `.assert expr, error, "message"` | Assembly assertion, evaluated when resolvable |
| `.assert expr, lderror, "message"` | Assertion checked after final emission |

Unknown active directives are errors. This is not a mechanism for silently
discarding unsupported ca65 functionality.

## 6. Two-pass assembly in detail

### 6.1 Before Pass 1

`assemble_program()` validates `origin` and `max_size`, then preprocesses the
source once. It initializes `pc=origin`, a final symbol dictionary, a definition
set for duplicate detection, export declarations, pending equates, assertions
and an ordered list of emission records.

The default origin is `$0200`, matching [isa_test.cfg][config]. The default
maximum size is `$0E00` bytes. The public API allows another integer origin below
`$1000` and a nonnegative size limit; the reserved data boundary remains fixed.

### 6.2 Pass 1 fixes addresses and record sizes

For each expanded source record:

1. A label is assigned the current byte PC. Two different names may refer to
   the same address; defining the same name twice is an error.
2. An equate is evaluated if possible. An unresolved identifier puts it into
   the pending list, retaining the PC at the assignment for any `*` expression.
3. An instruction is parsed by `_instruction()`. Its addressing mode and
   therefore its length are fixed in an `_Instruction` record.
4. `.byte` and `.word` create `_Data` records with fixed element widths. Their
   final values may remain unresolved without affecting record size.
5. `.res` and `.align` require known counts/alignment and fill values at this
   point. They create `_Fill` records with an already fixed byte count.
6. Exports and assertions are recorded or evaluated as described below.

The local `reserve()` function advances PC and checks bounds for instructions,
data and padding alike. The image length must not exceed `max_size`, and its
exclusive end must not exceed `$1000`. Thus `$0FFF` can hold the final generated
byte; a larger custom size limit cannot authorize writing CODE into `$1000`.
These bounds apply to emitted bytes, not to equates identifying scratch RAM
such as `final_result=$2004`.

### 6.3 Forward symbols and stable widths

A forward label need not have a value in Pass 1 if the instruction length can
already be fixed. For example, `jmp later` always reserves three bytes, and
`bne later` always reserves two. Their operand values are filled in later.

Direct loads have a genuine sizing choice. If `later` is unresolved in
`lda later`, the assembler reserves the absolute form when legal. It does not
substitute zero and later discover that a two-byte instruction must grow.
Pass 2 never shrinks an absolute instruction after learning that an operand is
small; doing so would invalidate later labels and branch offsets.

This policy is observable even with a forward equate:

```asm
    lda address
address = $40
    lda address
```

The bytes are `AD 40 00 A5 40`: the first load's width was frozen before the
equate became known. Pending equates are resolved only after the complete layout
scan, so an earlier pending alias is not retried between later instructions.
This is conservative layout, not a general relaxation algorithm.

After layout, the pending-equate loop evaluates all newly resolvable entries
until none remain. If a pass makes no progress, it reports an undefined or cyclic
equate. This loop changes values only; it never recalculates record sizes.

### 6.4 Alignment and padding

Alignment is relative to the segment start, as in the reference output:

```text
padding_count = (-(pc - origin)) % alignment
```

Supported alignments are integers `1..65536`, including non-powers of two.
Fill bytes must be `0..255`; reserve counts must be nonnegative. Checks run
before allocating the emitted padding bytes.

With origin `$0201`, one byte followed by `.align 4, $CC` inserts three bytes,
placing the next label at `$0205`. It does not align the absolute address to
`$0204`. The formal page-boundary tests use origin `$0200` and alignment `$100`,
so segment-relative alignment also gives the intended absolute page boundaries.

### 6.5 Assertions, exports and Pass 2

`error` and `lderror` are not silently treated as identical tokens:

- A resolvable `error` assertion is checked during the layout scan. A false
  value raises `AssemblyError` immediately with its message and source.
- An `error` expression containing forward symbols is checked after final
  symbol resolution, before operand emission.
- All exported names must exist in the final symbol dictionary.
- Pass 2 calls `_listing_entry()` on the ordered records. `_encode()` resolves
  instruction operands and branch displacements; `_Data` expressions resolve
  to checked byte/word values; `_Fill` records emit their fixed fill bytes.
- `lderror` assertions are checked after successful emission. Each uses the PC
  saved at its own directive, not the final program end unless placed there.
- The emitted chunks are joined into `code` and returned with symbols and exports.

For each data element, `_listing_entry()` supplies `record.address + bytes_so_far`
as its expression PC. Therefore `.byte <*,<*` at `$0200` emits `00 01`, and the
following `.word *,*` emits `02 02 04 02`.

There is no relocatable object format or independent linker in this process.
Both assertion modes ultimately use the same resolved integer addresses.
Their conditions are enforced, but every ca65-versus-ld65 diagnostic stage is
not reproduced: ca65 can defer a relocation-dependent `error` assertion until
linking, while this assembler already knows its requested absolute origin.

### 6.6 Worked layout and emission example

This complete small example exercises a forward branch, a backward absolute
jump, zero-page selection, padding and symbolic word data:

```asm
slot = $40
.export start, done, pointer
start:
    lda #1
    sta slot
    bne done
    .byte $AA
    .align 4, $CC
done:
    jmp start
pointer:
    .word done
.assert done-start = 8, lderror, "wrong layout"
```

With the default origin, Pass 1 produces:

| Address | Record | Fixed size | Next PC |
| --- | --- | --- | --- |
| `$0200` | `lda #1`, `IMM` | 2 | `$0202` |
| `$0202` | `sta slot`, `Z` because `slot=$40` | 2 | `$0204` |
| `$0204` | `bne done`, unresolved target | 2 | `$0206` |
| `$0206` | `.byte $AA` | 1 | `$0207` |
| `$0207` | `.align 4,$CC` | 1 | `$0208` |
| `$0208` | `jmp start`, `ABS` | 3 | `$020B` |
| `$020B` | `.word done` | 2 | `$020D` |

The symbol dictionary contains `slot=$0040`, `start=$0200`, `done=$0208` and
`pointer=$020B`; only the last three are exported. Equates, labels, exports and
the assertion do not consume bytes.

Pass 2 resolves the branch as `$0208-($0204+2)=2`, the JMP operand as `$0200`, and
the word value as `$0208`. The assertion succeeds because `done-start=8`:

```text
$0200  A9 01       lda #1
$0202  85 40       sta slot
$0204  D0 02       bne done
$0206  AA          raw byte
$0207  CC          alignment fill
$0208  4C 00 02    jmp start
$020B  08 02       word containing done

Complete 13-byte image: A9 01 85 40 D0 02 AA CC 4C 00 02 08 02
```

## 7. Expression evaluation

[asm_expressions.py][expressions] implements a tokenizer and a precedence-climbing
parser, not Python `eval`. `_tokenize()` recognizes decimal integers, `$`-prefixed
hexadecimal integers, case-sensitive identifiers, parentheses and the supported
operator tokens. `_Parser.prefix()` handles literals, names, `*`, parentheses
and unary operators. `_Parser.expression(minimum)` consumes binary operators
whose binding strength meets the current threshold. Parsing the right operand
with `precedence + 1` makes binary operators at the same level left-associative.

The implemented precedence, highest first, is:

| Binding level | Operators |
| --- | --- |
| 60 | Unary `+`, `-`, `<` (low byte), `>` (high byte) |
| 50 | Binary `&`, `^`, at the same level |
| 40 | Binary `+`, `-` |
| 20 | Comparisons `=`, `<>`, `<`, `>`, `<=`, `>=` |
| 10 | Boolean `.and` |

Comparisons and `.and` return integer 0 or 1. Both operands of `.and` are
evaluated, so it cannot hide an undefined symbol through short-circuiting.
In prefix position `<`/`>` extract bytes; between expressions they compare.
`*` is a current-location primary, not multiplication.

Examples using `saved_a=$2010`, `landing=$1234` and `number=15`:

| Expression | Value | Explanation |
| --- | --- | --- |
| `255` or `$FF` | `$FF` | Decimal or hexadecimal literal |
| `saved_a+1` | `$2011` | Symbol arithmetic |
| `<(landing-1)` | `$33` | Low byte of `$1233` |
| `>(landing-1)` | `$12` | High byte of `$1233` |
| `*-start`, with PC `$0230`, start `$0200` | `$30` | Distance in bytes |
| `number >= 1 .and number <= 255` | 1 | Protocol case-number check |
| `1+2 & 2 ^ 1` | 4 | `1 + ((2 & 2) ^ 1)` |
| `1 ^ 3 & 2` | 2 | `(1 ^ 3) & 2` |

Parentheses matter for byte extraction: `<$12FF+1` means `(<$12FF)+1`, giving
`$0100`; `<($12FF+1)` gives `$00`. The former would fail if used as an unmasked
one-byte operand. The bitwise/additive precedence was corrected during Phase 2
using independent ca65 probes; the original ADC image was unaffected.

`evaluate()` raises `UndefinedSymbolError` with a `name` field for an unavailable
identifier. Assembly uses that distinction to defer forward instruction operands
or equates. Preprocessing instead requires already-defined constants for active
conditions/counts. Malformed expressions, unsupported characters/operators,
unbalanced parentheses and excessive nesting raise `ExpressionError`.
`_value()` wraps expression errors as source-aware `AssemblyError` instances.

The supported expression subset excludes character/string literals, `%` binary
literals, `0x` assembler literals, multiplication, division and additional
ca65 operators. Recognition of quoted text by comment/macro processing does not
make strings valid numeric operands.

## 8. Complete ADC assembly walkthrough

The unchanged [test_arith_ADC.asm][adc] and [test_protocol.inc][protocol] were
David's first compatibility target. The file contains 15 binary-mode ADC
scenarios: eight immediate arithmetic cases and seven memory-mode cases,
together exercising all eight ADC addressing modes. Its helper checks are
assembly code too and must be encoded with the same accuracy as the target.

### 8.1 Include and protocol definitions

The source selects CPU `6502`, includes `test_protocol.inc`, exports its entry,
completion and scratch symbols, and selects CODE. The include guard is active
on its first encounter. It contributes these equates and exports:

```asm
TEST_PROTOCOL_INCLUDED = 1
test_case    = $2003
final_result = $2004
.export test_case, final_result
```

These assignments allocate no memory in the CODE image. They tell the test
program and eventual runner where the protocol bytes reside. The ADC source
similarly defines `saved_a=$2010` and `saved_p=$2011` for its checking code.

### 8.2 Startup and case-number macro

The beginning of the actual verified image is:

| Address | Source | Bytes |
| --- | --- | --- |
| `$0200` | `start: ldx #$FF` | `A2 FF` |
| `$0202` | `txs` | `9A` |
| `$0203` | `cld` | `D8` |
| `$0204` | `lda #0` | `A9 00` |
| `$0206` | `sta final_result` | `8D 04 20` |

The first `TEST_CASE 1` invocation expands into:

```asm
.assert 1 >= 1 .and 1 <= 255, error, "case must fit in one byte"
    lda #1
    sta test_case
```

The assertion emits no bytes. The load is at `$0209` (`A9 01`) and the store at
`$020B` (`8D 03 20`). The following `cld`, `clc`, `lda #$12` occupy `$020E`,
`$020F` and `$0210`; therefore `probe_1=$0212`, where `adc #$34` emits `69 34`.

### 8.3 Nested checking macro and real branch targets

The source's `CHECK_ADC $46, $00` invocation expands completely to:

```asm
    php
    sta saved_a
    pla
    sta saved_p
    and #$CB
    cmp #$00
    beq __asm_local_3_ok
    jmp fail
__asm_local_3_ok:
    lda saved_a
    cmp #$46
    beq __asm_local_4_ok
    jmp fail
__asm_local_4_ok:
```

`TEST_CASE` consumed macro serial 1, `CHECK_ADC` serial 2, and the two nested
`CHECK_A` calls serials 3 and 4. The real emitted checks are:

| Address | Expanded instruction or label | Bytes |
| --- | --- | --- |
| `$0214` | `php` | `08` |
| `$0215` | `sta saved_a` | `8D 10 20` |
| `$0218` | `pla` | `68` |
| `$0219` | `sta saved_p` | `8D 11 20` |
| `$021C` | `and #$CB` | `29 CB` |
| `$021E` | `cmp #$00` | `C9 00` |
| `$0220` | `beq __asm_local_3_ok` | `F0 03` |
| `$0222` | `jmp fail` | `4C A8 04` |
| `$0225` | `__asm_local_3_ok: lda saved_a` | `AD 10 20` |
| `$0228` | `cmp #$46` | `C9 46` |
| `$022A` | `beq __asm_local_4_ok` | `F0 03` |
| `$022C` | `jmp fail` | `4C A8 04` |
| `$022F` | `__asm_local_4_ok:` and `passed_1:` | No bytes |

For the first BEQ, the label value `$0225` is resolved after layout and the
offset is `$0225-($0220+2)=3`. Its three skipped bytes are the JMP to `fail`.
The second branch similarly lands at `$022F`.

When executed, PHP captures status before comparison/load helpers change flags.
The saved accumulator and status are checked separately. Mask `$CB` selects
N/V/D/Z/C; for binary `$12+$34` with clear carry the fixed expectations are
A=`$46` and masked status=`$00`. This explains the source's checking logic;
assembling it does not itself validate ADC or the helpers on a CPU.

### 8.4 All ADC addressing forms in the actual image

| Probe | Address | Original instruction | Bytes |
| --- | --- | --- | --- |
| `probe_1` | `$0212` | `adc #$34` | `69 34` |
| `probe_9` | `$0346` | `adc $40` | `65 40` |
| `probe_10` | `$0377` | `adc $FF,x` | `75 FF` |
| `probe_11` | `$03A2` | `adc $1000` | `6D 00 10` |
| `probe_12` | `$03D5` | `adc $12FF,x` | `7D FF 12` |
| `probe_13` | `$0408` | `adc $13FF,y` | `79 FF 13` |
| `probe_14` | `$0449` | `adc ($60,x)` | `61 60` |
| `probe_15` | `$0483` | `adc ($70),y` | `71 70` |

For example, the encoded `$12FF` remains the base operand; X=1 and the resulting
runtime access to `$1300` are set up and checked by the test, not calculated by
the assembler. The same separation applies to zero-page wrapping and indirect
pointer reads. No CPU addressing defect is compensated for during encoding.

### 8.5 Final image, exports and PASS/FAIL reporting

The completed ADC image contains 688 bytes (`$02B0`), covering `$0200..$04AF`;
its exclusive end is `$04B0`. There are 321 instruction encodings, including
15 ADC instructions and 30 relative branches. It uses no data/padding directives,
so these 321 entries cover every image byte.

Its 36 exports are `start`, `end`, `saved_a`, `saved_p`, `test_case`,
`final_result`, and the 30 `probe_1..15` / `passed_1..15` names. Selected values:

| Symbol | Address |
| --- | --- |
| `start` | `$0200` |
| `probe_1` | `$0212` |
| `passed_1` | `$022F` |
| `passed_15` | `$04A0` |
| `end` | `$04A5` |
| `test_case` / `final_result` | `$2003` / `$2004` |
| `saved_a` / `saved_p` | `$2010` / `$2011` |

The unexported `success` and `fail` labels also appear in `result.symbols`:

```text
$04A0  A9 01       success: lda #1
$04A2  8D 04 20             sta final_result
$04A5  4C A5 04    end:     jmp end
$04A8  A9 FF       fail:    lda #255
$04AA  8D 04 20             sta final_result
$04AD  4C A5 04             jmp end
```

At runtime, successful checks fall through to `success`, while a failed check
jumps to `fail`. Both paths write the protocol status before reaching `end`.
The current shared runner's `execute_test()` waits for a retirement boundary
with PC equal to the exported `end`; it then accepts 1 as PASS, 255 as FAIL,
and classifies any other status as a protocol ERROR. Failure to reach `end`
within the clock budget is TIMEOUT. The self-loop instruction is included in
the image even though the runner can stop before executing it.

A successful `assemble_file()` call establishes none of those runtime outcomes.
Phase 3 must load `code[offset]` at `origin+offset`, supply the returned symbols
to the existing validation/execution path and preserve fresh CPU/memory creation,
retirement gating and strict status checks. This is a future integration contract,
not an already available runner API taking `AssemblyResult`.

## 9. Validation and correctness evidence

The following figures were checked against saved reports, JSON records, unit
logs and binary/label artifacts during preparation of this document. No full
CPU regression or external rebuild was needed for this documentation task.

| Verification | Confirmed result |
| --- | --- |
| Phase 1 unchanged ADC image | 688 bytes, exact ca65/ld65 match |
| Phase 1 exported symbols | 36 names and addresses matched exactly |
| Phase 1 instruction boundaries and bytes | 321/321 matched |
| Phase 1 branch displacements | 30/30 matched; each is +3 |
| Phase 1 focused unit-test log | 32 tests passed, no failures/errors |
| Phase 2 direct formal `.asm` inventory | 40 files |
| Phase 2 complete images and lengths | 40/40 exact matches, 45,736 bytes total |
| Phase 2 exported symbol maps | 40/40 exact matches, 1,398 entries across files |
| Phase 2 image sizes | 176–2,839 bytes |
| Phase 2 focused unit-test log | 52 tests passed, no failures/errors |
| Unresolved corpus differences | None recorded or found in the saved outputs |

The Phase 2 symbol total counts entries across files, not 1,398 globally unique
names. The 40 comparisons concern the files directly under `test/isa_tests/isa/`,
not diagnostic copies under historical results directories.

### Independent checks and error cases

[test_assembly.py][tests] retains the Phase 1 checks and adds focused tests for
the Phase 2 features. The earlier unsupported-directive check now uses syntax
that remains unsupported. Tests include:

- Literal NMOS byte vectors for all eight ADC forms and helper encodings,
  rather than expected values derived from the shared opcode table.
- Forward/backward labels, little-endian operands, value-based zero-page
  selection and conservative unresolved-operand widths.
- Relative limits +127/-128 and rejection of +128/-129, including padding.
- Include guards, nested macros, fresh locals, conditionals, repeated blocks
  and iterator scope, with invalid nesting and undefined-control checks.
- Raw bytes/words, forward data values, current PC per data element, fill
  bytes, segment-relative alignment and invalid ranges.
- Duplicate/undefined symbols, cyclic equates, unsupported modes/directives,
  CODE overflow and protection of `$1000` even with an increased size limit.
- Layout-dependent assertions and the ordering of `error` versus `lderror`.
- `test_public_file_api_never_calls_external_assembler_or_fallback()`, which
  blocks `subprocess.run`, `subprocess.Popen` and `shutil.which` while assembling
  include/macro/conditional/repeat/data syntax through `assemble_file()`.

Independent ca65 probes additionally established the bitwise precedence,
per-element PC, unsigned data ranges, default-zero fill and segment-relative
alignment semantics. Successful examples and explicit invalid-input tests serve
different purposes: matching valid corpus output alone would not prove that
out-of-range or malformed source is rejected correctly.

### Retained development records

These local result directories contain the historical evidence; they are not
runtime dependencies or required source files for using the Python API:

```text
test/isa_tests/results/assembler_phase1_2026-10-28_02/
    REPORT.md, summary.json, unit_tests.log
    reference.bin/.lbl/.lst, python.bin, python_listing.json

test/isa_tests/results/assembler_phase2_2026-10-28_01/
    REPORT.md, summary.json, reference_summary.json
    unit_tests.log, unit_tests.json
    reference/<test>/
    comparison_01/<test>/
    oracle_probes_01/
```

The Phase 2 comparator builds each unchanged source using ca65/ld65, reads its
reference bytes and exported labels, then independently calls `assemble_file()`.
It compares lengths, every byte and exported names/addresses. A mismatch record
has the first byte offset, absolute address and expected/actual values, including
missing trailing bytes; symbol differences have separate missing/extra/changed
fields. A file error does not prevent comparisons of later files.

All 80 reference build commands retain their outputs and successful exit codes.
Saved-reference reuse checks source/protocol/configuration and reference artifact
fingerprints, so it cannot silently compare against changed inputs. During this
documentation review, the 40 saved Python images and independently parsed export
maps were rechecked against their saved references. All matched. Short worked
examples in this document were also checked in memory without creating files.

The focused tests can be repeated from the project environment:

```text
python -B -m unittest discover -s test/isa_tests -p test_assembly.py -v
```

ca65/ld65 are a development reference for binary compatibility. They are not
called by the Python assembler or its unit tests. Exact agreement on these
40 programs is evidence for this source corpus, not a proof of every possible
ca65 program or of CPU instruction semantics.

## 10. Limits and the separate Phase 3 step

The current implementation deliberately supports the formal tests' language
subset. Important limits follow directly from the code:

| Boundary | Actual behavior |
| --- | --- |
| Segments and linking | One CODE segment; no imports, relocation records, object-file output or general linker configuration |
| Origin and data region | API placement argument; no `.org`; generated CODE cannot enter `$1000` |
| Layout decisions | Known values and legal forms select zero page; unresolved forms reserve absolute width when available; no relaxation or address-size overrides |
| Conditional/repeat values | Already-resolved preprocessing constants only; no label/PC-dependent or retrospectively resolved controls |
| Padding | Count/alignment/fill must be known when encountered in layout |
| Macros | Fixed positional parameters; no nested definitions, default/variadic arguments or general ca65 scopes/token concatenation |
| Local identifiers | Generated `__asm_local_*` names are ordinary symbols; authors should avoid that prefix; duplicate definitions fail |
| Expressions and data | Integer subset described above; no strings/characters in `.byte/.word`, binary includes or complete ca65 operator language |
| Additional directives | `.ifdef`, `.elseif`, `.incbin`, `.proc`, other segments and unknown active directives are rejected |
| Assertion stages | Enforced conditions with immediate/deferred checks, but no full object-relocation model reproducing every ca65/ld65 diagnostic stage |
| Validation scope | Exact output for the current 40 files plus focused tests; not exhaustive validation of all catalog forms or CPU behavior |

One further distinction matters when reading historical reports: Phase 1's
expression precedence and assertion timing were subsequently refined in Phase 2.
The current algorithms described here take precedence over historical descriptions.
No corpus mismatch remains, but general language compatibility beyond the tested
subset should not be inferred from that result.

Phase 3 will be a separate runner change: replace external build/label-file
consumption with the in-memory bytes and symbol mapping while retaining protocol
validation, program placement, independent CPU/memory instances, retirement-based
completion, timeouts and per-file reporting. SingleCycle and MultiCycle execution
will still need their existing model-specific adapters and supported-instruction
checks. An assembler capable of encoding an instruction cannot make a CPU that
lacks that instruction execute the formal test.

No runner integration or CPU execution result is claimed by this design document.

[assembly]: ../punxa_6502/assembly.py
[frontend]: ../punxa_6502/asm_frontend.py
[expressions]: ../punxa_6502/asm_expressions.py
[opcodes]: ../punxa_6502/instruction_decode.py
[tests]: ../test/isa_tests/test_assembly.py
[adc]: ../test/isa_tests/isa/test_arith_ADC.asm
[protocol]: ../test/isa_tests/isa/test_protocol.inc
[config]: ../test/isa_tests/isa_test.cfg
[runner]: ../test/isa_tests/tb_ISA_tests.py
