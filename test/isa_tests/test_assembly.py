"""CPU-free checks for the Python assembler; expected bytes are fixed vectors.

These checks deliberately neither invoke ca65/ld65 nor derive their oracle from
the project's decoder. They do not count as ISA CPU execution coverage.
"""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from punxa_6502.assembly import (
    AssemblyError, AssemblyResult, assemble_file, assemble_program,
)
from punxa_6502.asm_expressions import ExpressionError, evaluate


class InstructionEncodingTests(unittest.TestCase):
    def test_all_eight_adc_modes_have_fixed_nmos_encodings(self):
        vectors = (
            ("adc #$12", "69 12"),
            ("adc $40", "65 40"),
            ("adc $FF,x", "75 FF"),
            ("adc $1234", "6D 34 12"),
            ("adc $12FF,x", "7D FF 12"),
            ("adc $13FF,y", "79 FF 13"),
            ("adc ($60,x)", "61 60"),
            ("adc ($70),y", "71 70"),
        )
        for source, expected in vectors:
            with self.subTest(source=source):
                self.assertEqual(assemble_program(source).code,
                                 bytes.fromhex(expected))

    def test_adc_helpers_have_independent_fixed_encodings(self):
        vectors = (
            ("cmp #$CB", "C9 CB"),
            ("beq $0202", "F0 00"),
            ("jmp $0200", "4C 00 02"),
            ("php", "08"),
            ("pla", "68"),
            ("sta $2010", "8D 10 20"),
            ("and #$CB", "29 CB"),
            ("lda #$FF", "A9 FF"),
            ("lda $2010", "AD 10 20"),
            ("ldx #$FF", "A2 FF"),
            ("ldy #2", "A0 02"),
            ("txs", "9A"),
            ("cld", "D8"),
            ("clc", "18"),
            ("sec", "38"),
            ("stx $40", "86 40"),
            ("stx $1000", "8E 00 10"),
        )
        for source, expected in vectors:
            with self.subTest(source=source):
                self.assertEqual(assemble_program(source).code,
                                 bytes.fromhex(expected))

    def test_width_is_chosen_by_value_and_available_mode(self):
        result = assemble_program("lda $0040\nlda $40\nlda $0100\n"
                                  "lda $40,y\nldx $40,y\njmp $40")
        # LDA has no zp,Y and JMP has no zero-page form; LDX does have zp,Y.
        self.assertEqual(result.code, bytes.fromhex(
            "A5 40 A5 40 AD 00 01 B9 40 00 B6 40 4C 40 00"))

    def test_forward_code_label_freezes_absolute_width(self):
        result = assemble_program("lda later\nlda #1\nlater: clc\n"
                                  "jmp later")
        self.assertEqual(result.symbols["later"], 0x0205)
        self.assertEqual(result.code,
                         bytes.fromhex("AD 05 02 A9 01 18 4C 05 02"))

    def test_byte_addressed_origin_and_little_endian_operands(self):
        result = assemble_program("start: lda #1\njmp start", origin=0x0300)
        self.assertIsInstance(result, AssemblyResult)
        self.assertEqual(result.origin, 0x0300)
        self.assertIsInstance(result.code, bytes)
        self.assertEqual(result.symbols["start"], 0x0300)
        self.assertEqual(result.code, bytes.fromhex("A9 01 4C 00 03"))

    def test_accumulator_and_indirect_jump_encodings(self):
        self.assertEqual(assemble_program("ror a\njmp ($12FF)").code,
                         bytes.fromhex("6A 6C FF 12"))

    def test_case_insensitive_instruction_and_index_register(self):
        self.assertEqual(assemble_program("ADC ($60,X)\nLdA #$a5").code,
                         bytes.fromhex("61 60 A9 A5"))

    def test_invalid_instructions_modes_and_ranges_raise(self):
        for source in (
            "not_an_instruction", "sta #1", "stx $1000,x",
            "adc #256", "adc #-257", "lda $10000", "lda -1",
            "adc ($100,x)", "adc ($100),y", "lda #1, x",
            "adc ($40),x", "lda ($1234),x",
        ):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)


class LabelAndLayoutTests(unittest.TestCase):
    def test_forward_and_backward_relative_displacements(self):
        result = assemble_program("start: clc\nbeq finish\nsec\n"
                                  "finish: bne start")
        self.assertEqual(result.code, bytes.fromhex("18 F0 01 38 D0 FA"))
        self.assertEqual(result.symbols["finish"], 0x0204)

    def test_forward_relative_limit_and_rejection(self):
        source = "bne target\n" + "clc\n" * 127 + "target: sec"
        self.assertEqual(assemble_program(source).code[:2], b"\xD0\x7F")
        with self.assertRaises(AssemblyError):
            assemble_program("bne target\n" + "clc\n" * 128 + "target: sec")

    def test_backward_relative_limit_and_rejection(self):
        source = "target:\n" + "clc\n" * 126 + "bne target"
        self.assertEqual(assemble_program(source).code[-2:], b"\xD0\x80")
        with self.assertRaises(AssemblyError):
            assemble_program("target:\n" + "clc\n" * 127 + "bne target")

    def test_constants_exported_equates_and_end_label(self):
        result = assemble_program(".setcpu \"6502\"\n.segment \"CODE\"\n"
                                  "test_case=$2003\nfinal_result=$2004\n"
                                  ".export test_case, final_result, start, end\n"
                                  "start: lda #1\nsta final_result\nend: jmp end")
        self.assertEqual(result.exports,
                         frozenset(("test_case", "final_result", "start", "end")))
        self.assertEqual({key: result.symbols[key] for key in result.exports},
                         {"test_case": 0x2003, "final_result": 0x2004,
                          "start": 0x0200, "end": 0x0205})
        self.assertEqual(result.code, bytes.fromhex("A9 01 8D 04 20 4C 05 02"))

    def test_forward_low_and_high_byte_expressions(self):
        result = assemble_program("lda #<(landing-1)\nldx #>(landing-1)\n"
                                  "landing: clc")
        self.assertEqual(result.code, bytes.fromhex("A9 03 A2 02 18"))

    def test_forward_equate_keeps_conservative_absolute_width(self):
        # Resolving the later equate must not shrink the first instruction and
        # move the branch/labels after layout has already fixed their addresses.
        result = assemble_program("lda address\nbeq finish\naddress=$40\n"
                                  "finish: lda address")
        self.assertEqual(result.symbols["address"], 0x40)
        self.assertEqual(result.symbols["finish"], 0x0205)
        self.assertEqual(result.code, bytes.fromhex("AD 40 00 F0 00 A5 40"))

    def test_cyclic_equates_are_rejected(self):
        for source in ("first=second\nsecond=first\nlda first",
                       "first=first+1\nlda first"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)

    def test_deferred_assertion_and_requested_error_message(self):
        source = (".assert end-start = 2, lderror, \"wrong width\"\n"
                  "start: lda #0\nend:")
        self.assertEqual(assemble_program(source).code, bytes.fromhex("A9 00"))
        with self.assertRaisesRegex(AssemblyError, "wrong width"):
            assemble_program(source.replace("= 2", "= 3"))

    def test_undefined_and_duplicate_symbols_are_errors(self):
        for source in ("jmp missing", ".export missing\nclc",
                       "again: clc\nagain: sec", "x=1\nx=2\nclc"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)

    def test_code_capacity_boundary(self):
        self.assertEqual(assemble_program("clc\nsec", max_size=2).code,
                         b"\x18\x38")
        with self.assertRaises(AssemblyError):
            assemble_program("clc\nsec\nclc", max_size=2)

    def test_default_code_region_does_not_overlap_data_at_1000(self):
        self.assertEqual(len(assemble_program("clc\n" * 0x0E00).code), 0x0E00)
        with self.assertRaises(AssemblyError):
            assemble_program("clc\n" * 0x0E01)

    def test_increased_size_limit_does_not_relax_reserved_data_boundary(self):
        self.assertEqual(assemble_program("clc", origin=0x0FFF, max_size=2).code,
                         b"\x18")
        with self.assertRaises(AssemblyError):
            assemble_program("clc\nsec", origin=0x0FFF, max_size=2)
        with self.assertRaises(AssemblyError):
            assemble_program("clc", origin=0x1000, max_size=1)

    def test_invalid_layout_arguments(self):
        for arguments in ({"origin": -1}, {"origin": 0x10000},
                          {"max_size": -1}, {"origin": 0xFFFF, "max_size": 2}):
            with self.subTest(arguments=arguments):
                with self.assertRaises(AssemblyError):
                    assemble_program("clc", **arguments)


class PreprocessorTests(unittest.TestCase):
    def test_nested_macros_and_fresh_local_labels(self):
        source = """
.macro INNER value
    .local done
    lda #value
    beq done
    lda #0
done:
.endmacro
.macro OUTER value
    INNER value
.endmacro
OUTER 1
OUTER 2
"""
        self.assertEqual(assemble_program(source).code,
                         bytes.fromhex("A9 01 F0 02 A9 00 A9 02 F0 02 A9 00"))

    def test_macro_arguments_replace_whole_symbols_only(self):
        source = """
value_copy=$2010
.macro COPY value
    lda #value
    sta value_copy
.endmacro
COPY 3
"""
        self.assertEqual(assemble_program(source).code,
                         bytes.fromhex("A9 03 8D 10 20"))

    def test_assertions_in_parameterized_macro(self):
        source = """
.macro CASE number
    .assert number >= 1 .and number <= 255, error, "bad case number"
    lda #number
.endmacro
CASE 255
"""
        self.assertEqual(assemble_program(source).code, bytes.fromhex("A9 FF"))
        with self.assertRaisesRegex(AssemblyError, "bad case number"):
            # Zero fits LDA's operand but violates the macro's independent
            # protocol assertion, so no unrelated range error masks it.
            assemble_program(source.replace("CASE 255", "CASE 0"))

    def test_include_guard_prevents_second_macro_definition(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "protocol.inc").write_text("""
.ifndef INCLUDED
INCLUDED=1
status=$2004
.export status
.macro STORE value
    lda #value
    sta status
.endmacro
.endif
""", encoding="utf-8")
            program = folder / "main.asm"
            program.write_text('.include "protocol.inc"\n'
                               '.include "protocol.inc"\nSTORE 1\n', encoding="utf-8")
            result = assemble_file(program)
            self.assertEqual(result.code, bytes.fromhex("A9 01 8D 04 20"))
            self.assertEqual(result.symbols["status"], 0x2004)

    def test_include_search_path_and_source_location_for_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "helper.inc").write_text(".macro LOAD\nlda #7\n.endmacro\n",
                                                encoding="utf-8")
            result = assemble_program('.include "helper.inc"\nLOAD',
                                      include_dirs=(folder,))
            self.assertEqual(result.code, bytes.fromhex("A9 07"))
            (folder / "broken.inc").write_text("lda #256\n", encoding="utf-8")
            with self.assertRaises(AssemblyError) as failure:
                assemble_program('.include "broken.inc"', include_dirs=(folder,))
            self.assertIn("broken.inc", str(failure.exception))

    def test_no_symbols_or_macros_leak_between_assembly_calls(self):
        assemble_program(".macro PRIVATE\nclc\n.endmacro\nPRIVATE")
        with self.assertRaises(AssemblyError):
            assemble_program("PRIVATE")
        with self.assertRaises(AssemblyError):
            assemble_program("lda #PRIVATE_SYMBOL")

    def test_bad_macro_calls_and_unterminated_blocks_raise(self):
        for source in (
            ".macro M a,b\nlda #a\n.endmacro\nM 1",
            ".macro M\nclc\n.endmacro\nM 1",
            ".macro M\nclc", ".ifndef X\nclc", ".endif",
            '.include "certainly_missing_assembler_file.inc"',
        ):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)

    def test_unsupported_directives_are_explicit_errors(self):
        for source in (".org $0200", '.incbin "unknown.bin"',
                       ".ifdef X\nclc\n.endif", ".elseif 1", ".proc name",
                       '.setcpu "65C02"', '.segment "BSS"'):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)


class DataAndExpansionTests(unittest.TestCase):
    def test_public_file_api_never_calls_external_assembler_or_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "protocol.inc").write_text("""
.ifndef INCLUDED
INCLUDED=1
status=$2004
.export status
.macro EMIT value
    .if value = 1
        .byte $A5
    .else
        .word status
    .endif
.endmacro
.endif
""", encoding="utf-8")
            program = folder / "main.asm"
            program.write_text("""
.include "protocol.inc"
.export start,end
start:
.repeat 2,index
    EMIT index
.endrepeat
end: clc
""", encoding="utf-8")
            forbidden = AssertionError("external assembler discovery/execution is forbidden")
            with (
                mock.patch("subprocess.run", side_effect=forbidden) as run,
                mock.patch("subprocess.Popen", side_effect=forbidden) as popen,
                mock.patch("shutil.which", side_effect=forbidden) as which,
            ):
                result = assemble_file(program)
            run.assert_not_called()
            popen.assert_not_called()
            which.assert_not_called()
            self.assertEqual(result.code, bytes.fromhex("04 20 A5 18"))
            self.assertEqual({name: result.symbols[name] for name in result.exports},
                             {"status": 0x2004, "start": 0x0200, "end": 0x0203})

    def test_nested_conditionals_use_macro_arguments_and_skip_inactive_code(self):
        source = """
.macro PICK outer, inner
    .if outer
        .if inner
            lda #1
        .else
            lda #2
        .endif
    .else
        lda #3
    .endif
.endmacro
PICK 1, 0
PICK 1, 1
PICK 0, never_defined
"""
        self.assertEqual(assemble_program(source).code,
                         bytes.fromhex("A9 02 A9 01 A9 03"))

    def test_if_expression_constants_and_unselected_unknown_expression(self):
        source = """
LIMIT=2
.if LIMIT >= 1 .and LIMIT <= 3
    .byte $AA
.else
    not_a_real_instruction
.endif
.if 0
    .if never_defined
        .byte invalid_value
    .endif
.else
    .byte $55
.endif
"""
        self.assertEqual(assemble_program(source).code, bytes.fromhex("AA 55"))

    def test_malformed_and_unresolved_conditionals_are_errors(self):
        for source in (".if 1\nclc", ".else", ".if unknown\nclc\n.endif",
                       ".if 1\n.else\n.else\n.endif", ".if\n.endif",
                       ".if later\nclc\n.endif\nlater=1"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)

    def test_repeat_zero_default_and_named_iterators(self):
        source = """
.repeat 0
    .byte unknown
.endrepeat
.repeat 2
    .byte $A5
.endrepeat
.repeat 3, index
    .byte index
.endrepeat
"""
        self.assertEqual(assemble_program(source).code,
                         bytes.fromhex("A5 A5 00 01 02"))

    def test_nested_repeats_and_macro_local_labels_remain_distinct(self):
        source = """
.macro LOAD value
    .local done
    lda #value
    bne done
    clc
done:
.endmacro
.repeat 2, index
    LOAD index+1
.endrepeat
.repeat 2, outer
    .repeat 2, inner
        .byte outer+inner
    .endrepeat
.endrepeat
"""
        self.assertEqual(assemble_program(source).code, bytes.fromhex(
            "A9 01 D0 01 18 A9 02 D0 01 18 00 01 01 02"))

    def test_repeat_iterator_does_not_escape_its_block(self):
        with self.assertRaises(AssemblyError):
            assemble_program(".repeat 2, index\n.byte index\n.endrepeat\n.byte index")

    def test_invalid_repeat_counts_and_blocks_are_errors(self):
        for source in (".repeat -1\nclc\n.endrepeat", ".repeat 2\nclc",
                       ".endrepeat", ".repeat unknown\nclc\n.endrepeat",
                       ".repeat 2, 3\nclc\n.endrepeat"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)

    def test_byte_and_word_values_use_fixed_little_endian_vectors(self):
        result = assemble_program(".byte $00,$7F,$80,$FF\n.word $0000,$1234,$FFFF")
        self.assertEqual(result.code, bytes.fromhex("00 7F 80 FF 00 00 34 12 FF FF"))

    def test_raw_jmp_encoding_and_forward_label_low_high_bytes(self):
        source = ".byte $6C\n.word $12FF\n.byte <landing,>landing\n.word landing\nlanding: clc"
        result = assemble_program(source)
        self.assertEqual(result.symbols["landing"], 0x0207)
        self.assertEqual(result.code, bytes.fromhex("6C FF 12 07 02 07 02 18"))

    def test_current_pc_and_equates_follow_byte_data_layout(self):
        result = assemble_program("start=*\n.byte <*\n.word *\nend:\n"
                                  '.assert end-start = 3, lderror, "byte layout"')
        self.assertEqual(result.code, bytes.fromhex("00 01 02"))
        self.assertEqual(result.symbols["end"], 0x0203)

    def test_current_pc_advances_for_each_data_element(self):
        result = assemble_program(".byte <*,<*\n.word *,*")
        self.assertEqual(result.code, bytes.fromhex("00 01 02 02 04 02"))

    def test_branch_displacements_include_raw_data_widths(self):
        result = assemble_program("start: bne finish\n.byte $AA,$BB\n.word start\n"
                                  "finish: bne start")
        self.assertEqual(result.code, bytes.fromhex("D0 04 AA BB 00 02 D0 F8"))

    def test_align_and_res_explicit_and_default_fill(self):
        source = (".byte $AA\n.align 4,$CC\n.byte $BB\n.align 4\n"
                  ".res 2,$DD\n.res 1\nend:")
        result = assemble_program(source)
        self.assertEqual(result.code,
                         bytes.fromhex("AA CC CC CC BB 00 00 00 DD DD 00"))
        self.assertEqual(result.symbols["end"], 0x020B)
        self.assertEqual(assemble_program(".res 0\n.align 1\nclc").code,
                         bytes.fromhex("18"))

    def test_alignment_is_segment_relative_even_at_unaligned_origin(self):
        result = assemble_program(".byte $AA\n.align 4,$CC\nlanding: .byte $BB",
                                  origin=0x0201)
        self.assertEqual(result.code, bytes.fromhex("AA CC CC CC BB"))
        self.assertEqual(result.symbols["landing"], 0x0205)
        self.assertEqual(assemble_program(".byte $AA\n.align 3,$CC\n.byte $BB").code,
                         bytes.fromhex("AA CC CC BB"))
        self.assertEqual(assemble_program(".align 65536\nclc").code, b"\x18")

    def test_padding_preserves_signed_branch_limits(self):
        forward = assemble_program("bne end\n.res 127\nend: clc")
        self.assertEqual(forward.code[:2], bytes.fromhex("D0 7F"))
        with self.assertRaises(AssemblyError):
            assemble_program("bne end\n.res 128\nend: clc")
        backward = assemble_program("start: .res 126\nbne start")
        self.assertEqual(backward.code[-2:], bytes.fromhex("D0 80"))

    def test_data_and_padding_cannot_enter_reserved_memory(self):
        for source in (".byte 1,2", ".word 1", ".res 2", ".align 4\n.res 2"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source, origin=0x0FFF, max_size=0x100)

    def test_invalid_data_padding_values_and_forward_sizes_are_errors(self):
        for source in (".byte 256", ".word $10000", ".byte unknown",
                       ".byte -1", ".word -1",
                       ".res -1", ".res 1,256", ".align 0", ".align -1",
                       ".align 65537", ".align 4,256", ".res later\nlater=2",
                       ".align later\nlater=4", ".byte", ".word", ".res"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    assemble_program(source)

    def test_layout_assertions_check_final_symbols_for_both_severities(self):
        for severity in ("error", "lderror"):
            source = ('.assert end-start = 4, ' + severity + ', "wrong width"\n'
                      "start: .byte 1\n.res 3\nend:")
            with self.subTest(severity=severity):
                self.assertEqual(assemble_program(source).code,
                                 bytes.fromhex("01 00 00 00"))
                with self.assertRaisesRegex(AssemblyError, "wrong width"):
                    assemble_program(source.replace("= 4", "= 5"))

    def test_error_assertion_precedes_emission_but_lderror_is_deferred(self):
        with self.assertRaisesRegex(AssemblyError, "assembly guard"):
            assemble_program('.assert 0, error, "assembly guard"\nlda missing')
        with self.assertRaisesRegex(AssemblyError, "undefined symbol: missing"):
            assemble_program('.assert 0, lderror, "link guard"\nlda missing')


class ExpressionTests(unittest.TestCase):
    def test_required_numeric_symbol_and_operator_vectors(self):
        symbols = {"value": 0x81, "landing": 0x1234, "number": 255}
        vectors = (
            ("255", 255), ("$FF", 255), ("value+2", 0x83),
            ("$0100+value-1", 0x180), ("(-value) & $FF", 0x7F),
            ("$F0 ^ $AA", 0x5A), ("<(landing-1)", 0x33),
            (">(landing-1)", 0x12), ("1+2-3", 0),
            ("number >= 1 .and number <= 255", 1),
            ("number = 255", 1), ("number <> 255", 0),
            ("number < 256", 1), ("number > 255", 0),
            ("number <= 254", 0), ("number >= 256", 0),
            # ca65 gives bitwise &,^ equal precedence, tighter than addition.
            ("1+2 & 2 ^ 1", 4), ("1 ^ 3 & 2", 2),
        )
        for expression, expected in vectors:
            with self.subTest(expression=expression):
                self.assertEqual(evaluate(expression, symbols), expected)

    def test_current_location(self):
        self.assertEqual(evaluate("*-start", {"start": 0x0200}, pc=0x0230), 0x30)

    def test_invalid_or_undefined_expressions_raise(self):
        for expression in ("unknown", "$GG", "1+", "(1", "1 2", "1/0",
                           "__import__('os')", "value.member"):
            with self.subTest(expression=expression):
                with self.assertRaises(ExpressionError):
                    evaluate(expression, {})


if __name__ == "__main__":
    unittest.main()
