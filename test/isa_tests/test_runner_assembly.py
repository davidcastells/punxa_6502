"""Focused in-memory runner integration checks, separate from formal ISA coverage.

Small temporary programs exercise the real assembler and SingleCycle runner.
The existing synthetic contracts cover retirement and protocol distinctions;
these checks cover their assembly-to-memory boundary without external tools.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from dataclasses import replace
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from punxa_6502.assembly import AssemblyResult
import tb_ISA_tests as tb


PROTOCOL_NAMES = frozenset(("test_case", "final_result", "end"))


def program(origin=0x0400):
    return AssemblyResult(
        origin, bytes.fromhex("EA EA 4C 01 04"),
        {"test_case": 0x2003, "final_result": 0x2004,
         "end": origin + 1, "extra": 0x2010},
        PROTOCOL_NAMES | {"extra"})


class PreparationTests(unittest.TestCase):
    def reject(self, result):
        # Invalid images must not construct partial hardware.
        with patch.object(tb.py4hw, "HWSystem",
                          side_effect=AssertionError("constructed invalid hardware")):
            with self.assertRaises((ValueError, TypeError)):
                tb.prepare_program(result)

    def test_byte_loading_origin_and_protocol_symbol_transfer(self):
        assembled = program()
        hw, cpu, memory, symbols = tb.prepare_program(assembled)
        self.assertEqual(cpu.pc, assembled.origin)
        self.assertEqual(memory.area[0][:2], (0, tb.MEMORY_SIZE))
        self.assertEqual(bytes(memory.readByte(assembled.origin + offset)
                               for offset in range(len(assembled.code))), assembled.code)
        self.assertEqual(memory.readByte(assembled.origin - 1), 0)
        self.assertEqual(memory.readByte(assembled.origin + len(assembled.code)), 0)
        self.assertEqual((memory.readByte(symbols["test_case"]),
                          memory.readByte(symbols["final_result"])), (0, 0))
        self.assertEqual(symbols, assembled.symbols)
        self.assertIsNot(symbols, assembled.symbols)
        symbols["extra"] = 0
        self.assertEqual(assembled.symbols["extra"], 0x2010)

    def test_each_preparation_has_fresh_hardware_cpu_and_memory(self):
        first = tb.prepare_program(program())
        first[2].writeByte(0x2010, 0xA5)
        second = tb.prepare_program(program())
        for old, new in zip(first[:3], second[:3]):
            self.assertIsNot(old, new)
        self.assertEqual(second[2].readByte(0x2010), 0)

    def test_adapter_receives_assembly_origin(self):
        observed = []
        sentinel = object()

        def create_cpu(*args):
            observed.append(args[-1])
            return sentinel

        result = tb.prepare_program(program(0x0600),
                                    adapter=SimpleNamespace(create_cpu=create_cpu))
        self.assertEqual(observed, [0x0600])
        self.assertIs(result[1], sentinel)

    def test_required_symbols_must_exist_and_be_exported(self):
        assembled = program()
        for name in PROTOCOL_NAMES:
            with self.subTest(name=name, problem="missing"):
                symbols = dict(assembled.symbols)
                symbols.pop(name)
                self.reject(replace(assembled, symbols=symbols))
            with self.subTest(name=name, problem="not exported"):
                self.reject(replace(assembled, exports=assembled.exports - {name}))

    def test_protocol_addresses_are_strict_16_bit_integers(self):
        for name in PROTOCOL_NAMES:
            for value in (-1, 0x10000, 0x2003 + 0.5, "8195", None, True):
                with self.subTest(name=name, value=value):
                    symbols = dict(program().symbols)
                    symbols[name] = value
                    self.reject(replace(program(), symbols=symbols))

    def test_empty_oversized_and_invalid_origin_images(self):
        for code in (b"", b"\xEA" * (tb.MEMORY_SIZE + 1), "\xEA", [0xEA],
                     bytearray(b"\xEA"), memoryview(b"1234").cast("H")):
            with self.subTest(code_type=type(code), size=len(code)):
                self.reject(replace(program(), code=code))
        for origin in (-1, tb.MEMORY_SIZE, 0.5, "512", True):
            with self.subTest(origin=origin):
                self.reject(replace(program(), origin=origin))
        self.reject(replace(program(), origin=0xFFFE))

    def test_memory_region_overlap_and_end_validation(self):
        for name in ("test_case", "final_result"):
            for address in (0x0400, 0x0404):
                with self.subTest(name=name, address=address):
                    symbols = dict(program().symbols)
                    symbols[name] = address
                    self.reject(replace(program(), symbols=symbols))
        self.reject(replace(program(), symbols={
            "test_case": 0x2004, "final_result": 0x2004, "end": 0x0401}))
        for address in (0x03FF, 0x0405):
            with self.subTest(end=address):
                symbols = dict(program().symbols)
                symbols["end"] = address
                self.reject(replace(program(), symbols=symbols))

    def test_legacy_label_reader_rejects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as directory:
            labels = Path(directory) / "labels.lbl"
            labels.write_text("al 002003 .test_case\nal 002004 .final_result\n"
                              "al 000201 .end\nal 000202 .end\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "[Dd]uplicate.*end"):
                tb.read_symbols(labels)

    def test_explicit_legacy_loaders_preserve_code_and_symbols(self):
        assembled = program(tb.PROGRAM_START)
        in_memory = tb.prepare_test(assembled)
        with tempfile.TemporaryDirectory() as directory:
            binary, labels = (Path(directory) / name
                              for name in ("legacy.bin", "legacy.lbl"))
            binary.write_bytes(assembled.code)
            labels.write_text("".join(f"al {value:06X} .{name}\n"
                                      for name, value in assembled.symbols.items()),
                              encoding="utf-8")
            from_files = tb.prepare_test(binary, labels)
        for prepared in (in_memory, from_files):
            _, cpu, memory, symbols = prepared
            self.assertEqual(cpu.pc, assembled.origin)
            self.assertEqual(symbols, assembled.symbols)
            self.assertEqual(bytes(memory.readByte(assembled.origin + offset)
                                   for offset in range(len(assembled.code))),
                             assembled.code)


class RunnerAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def source(self, name="test_data_tiny.asm", *, status=1, timeout=False):
        source = self.directory / name
        body = ("loop: jmp loop\n" if timeout else
                f"lda #{status}\nsta final_result\n")
        source.write_text('.setcpu "6502"\n.include "test_protocol.inc"\n'
                          '.export end\n.segment "CODE"\nTEST_CASE 7\n' +
                          body + "end: jmp end\n", encoding="utf-8")
        return source

    def test_build_returns_bytes_and_symbols_without_output_artifacts(self):
        source = self.source()
        unused = self.directory / "not-created"
        assembled = tb.build_test(source, unused, "obsolete-tool-directory")
        self.assertIsInstance(assembled, AssemblyResult)
        self.assertEqual(assembled.origin, 0x0200)
        self.assertEqual(assembled.symbols["test_case"], 0x2003)
        self.assertEqual(assembled.symbols["final_result"], 0x2004)
        self.assertTrue(PROTOCOL_NAMES <= assembled.exports)
        self.assertEqual(list(self.directory.iterdir()), [source])

    def test_normal_execution_needs_no_external_tools_or_output_files(self):
        source = self.source()
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {"PATH": ""}))
            for owner, name in ((subprocess, "run"), (subprocess, "Popen"),
                                (shutil, "which"), (tempfile, "TemporaryDirectory"),
                                (Path, "write_bytes"), (Path, "write_text"),
                                (Path, "mkdir")):
                stack.enter_context(patch.object(
                    owner, name, side_effect=AssertionError(f"unexpected {name}")))
            result = tb.run_file_result(source, cc65_bin="missing-tool-directory")
        self.assertEqual((result.outcome, result.case), ("PASS", 7), result.detail)
        self.assertEqual(list(self.directory.iterdir()), [source])

    def test_in_memory_pipeline_preserves_all_protocol_outcomes(self):
        for status, expected in ((1, "PASS"), (255, "FAIL"), (0, "ERROR"), (2, "ERROR")):
            with self.subTest(status=status):
                result = tb.run_file_result(self.source(status=status))
                self.assertEqual((result.outcome, result.case), (expected, 7), result.detail)
        result = tb.run_file_result(self.source(timeout=True), max_cycles=200)
        self.assertEqual((result.outcome, result.case, result.cycles), ("TIMEOUT", 7, 200))

    def test_assembly_and_protocol_preparation_errors_become_error(self):
        source = self.directory / "test_data_invalid.asm"
        for text, detail in (("not_an_instruction\n", "unknown instruction"),
                             (".export end\nend: jmp end\n", "test_case"),
                             ("same: nop\nsame: nop\n", "duplicate"),
                             ("jmp undefined_label\n", "undefined")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                result = tb.run_file_result(source)
                self.assertEqual(result.outcome, "ERROR")
                self.assertIn(detail, result.detail.lower())

    def test_trace_is_preserved_and_quiet_execution_suppresses_cpu_trace(self):
        source = self.source()
        for trace in (False, True):
            with self.subTest(trace=trace):
                output = io.StringIO()
                with redirect_stdout(output):
                    result = tb.run_file_result(source, trace=trace)
                self.assertEqual(result.outcome, "PASS", result.detail)
                if trace:
                    self.assertIn("0200 = 0xA9", output.getvalue())
                else:
                    self.assertEqual(output.getvalue(), "")

    def test_cli_selection_and_deprecated_option_warning(self):
        source = self.source()
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = tb.main([source.stem, "--test-dir", str(self.directory),
                            "--cc65-bin", "missing-tool-directory"])
        self.assertEqual(code, 0)
        self.assertIn("PASS:", output.getvalue())
        self.assertIn("deprecated", errors.getvalue().lower())
        self.assertIn("ignored", errors.getvalue().lower())

    def test_category_batch_continues_after_assembly_error_and_timeout(self):
        invalid = self.directory / "test_data_01_invalid.asm"
        invalid.write_text("invalid instruction\n", encoding="utf-8")
        self.source("test_data_02_timeout.asm", timeout=True)
        self.source("test_data_03_pass.asm")
        self.source("test_logic_not_selected.asm")
        with redirect_stdout(io.StringIO()):
            results = tb.runAllTests(self.directory, categories="data", max_cycles=200)
        self.assertEqual([result.outcome for result in results.values()],
                         ["ERROR", "TIMEOUT", "PASS"])
        self.assertEqual(tb.summarize_results(results)["total"],
                         {"PASS": 1, "FAIL": 0, "TIMEOUT": 1, "ERROR": 1,
                          "total": 3, "pass_rate": 100 / 3})


if __name__ == "__main__":
    unittest.main()
