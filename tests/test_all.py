# ============================================================================
# test_all.py  —  automated tests  ★ This whole file was written by our group
#
# How to run (in the main project folder):
#     python -m unittest discover -s tests -v
#
# Checks 5 things:
#   1. factorial.asm matches Python's math.factorial for every value 0-12,
#      and n = 13 must produce an overflow warning
#   2. nck.asm matches math.comb for every pair 0 <= k <= n <= 26 (378 cases)
#   3. the instructor's example programs (V7.1) still give the same results
#   4. machine code matches the answer key of course exercise A01 (= real MIPS)
#   5. labels, register names, $zero, and clear error messages
# ============================================================================

import io
import math
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))          # so files in sim/ can be imported

from cpu import CPU                             # noqa: E402
from memory import Memory                       # noqa: E402
from isa import Instruction, preprocess         # noqa: E402


def run_program(source_lines, inputs=""):
    """Run a program with fake input, return (cpu, text printed by the program)"""
    feed = iter(inputs.splitlines() or [""])
    fake_input = lambda prompt="": next(feed)  # noqa: E731
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        cpu = CPU(source_lines, Memory(), show_listing=False, input_func=fake_input, quiet=True)
        cpu.run()
    return cpu, "".join(cpu.output)


def read_lines(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8").splitlines()


class TestFactorial(unittest.TestCase):
    def test_all_values_0_to_12(self):
        program = read_lines("programs/factorial.asm")
        for n in range(13):
            with self.subTest(n=n):
                cpu, text = run_program(program, f"{n}")
                self.assertEqual(text.strip(), str(math.factorial(n)))
                self.assertEqual(cpu.overflows, [])
                self.assertEqual(cpu.registers[29], 0x8000)   # stack is back where it started (all allocations freed)

    def test_13_overflows(self):
        cpu, text = run_program(read_lines("programs/factorial.asm"), "13")
        self.assertTrue(cpu.overflows)                        # there must be a warning
        self.assertNotEqual(text.strip(), str(math.factorial(13)))


class TestNck(unittest.TestCase):
    def test_all_pairs_up_to_26(self):
        program = read_lines("programs/nck.asm")
        count = 0
        for n in range(27):
            for k in range(n + 1):
                with self.subTest(n=n, k=k):
                    cpu, text = run_program(program, f"{n} {k}")
                    self.assertEqual(text.strip(), str(math.comb(n, k)))
                    self.assertEqual(cpu.overflows, [])
                    count += 1
        self.assertEqual(count, 378)

    def test_k_out_of_range_gives_zero(self):
        program = read_lines("programs/nck.asm")
        for n, k in [(4, 7), (5, -1)]:
            with self.subTest(n=n, k=k):
                self.assertEqual(run_program(program, f"{n} {k}")[1].strip(), "0")


class TestTeacherPrograms(unittest.TestCase):
    """The instructor's example files must still run after our simulator changes"""

    def test_sum_10_to_1(self):
        cpu, _ = run_program(read_lines("examples/teacher_sum_10_to_1.txt"))
        self.assertEqual(cpu.registers[3], 55)
        self.assertIsNone(cpu.error)

    def test_instruction_test(self):
        cpu, _ = run_program(read_lines("examples/teacher_instruction_test.txt"))
        self.assertIsNone(cpu.error)
        self.assertEqual(cpu.registers[10], 31)       # ADDI $10 $11 -1  →  32 - 1
        self.assertEqual(cpu.registers[11], 32)       # ADDI $11 $0 32
        self.assertEqual(cpu.registers[9], 0)         # SLTIU $9 $11 1  →  32 < 1 ? no
        self.assertEqual(cpu.registers[3], 0)         # BNE jumps over ADDI $3 $0 99
        self.assertEqual(cpu.registers[21], 0)        # J 0x2030 jumps over ADDI $21 $0 6


class TestMachineCode(unittest.TestCase):
    """Compared with the answer key of exercise A01 (key-A01) = real MIPS machine code"""

    CASES = [
        ("LUI $s5, 0xA000",     "3c15a000"),   # answer 6.1
        ("ORI $s0, $zero, 0x27", "34100027"),  # answer 6.2
        ("SW $s0, 0($s5)",      "aeb00000"),   # answer 6.3
        ("LW $s1, 4($s5)",      "8eb10004"),   # answer 6.4
        ("J 0x00400050",        "08100014"),   # answer 6.5
        ("LW $s0, 4($s1)",      "8e300004"),   # answer 5.1
        ("SW $s0, -4($s1)",     "ae30fffc"),   # answer 5.2
        ("BEQ $t0, $s1, 2",     "11110002"),   # answer 5.3
        ("ADDI $s1, $s1, 1",    "22310001"),   # answer 5.3
        ("ADD $s2, $s1, $zero", "02209020"),   # answer 5.3 (R-type: the original V7.1 gave 00000000)
        ("JR $ra",              "03e00008"),
        ("SYSCALL",             "0000000c"),
        ("SLL $t3, $t2, 2",     "000a5880"),
    ]

    def test_encoding(self):
        for source, expected in self.CASES:
            with self.subTest(source=source):
                self.assertEqual(Instruction(source).hexcmd, expected)


class TestAssemblerFeatures(unittest.TestCase):
    def test_labels_and_register_names(self):
        program = [
            ".ORG 0x100",
            "start:  ORI $t0, $zero, 3   # count down from 3",
            "loop:   ADDI $t0, $t0, -1",
            "        BNE $t0, $zero, loop",
            "        J end",
            "        ORI $v0, $zero, 99  # this line must be skipped",
            "end:    HALT",
        ]
        lines, labels = preprocess(program)
        self.assertEqual(labels, {"start": 0x100, "loop": 0x104, "end": 0x114})
        self.assertIn("BNE $t0 $zero -2", lines)       # offset computed automatically
        cpu, _ = run_program(program)
        self.assertEqual(cpu.registers[8], 0)
        self.assertEqual(cpu.registers[2], 0)

    def test_zero_register_stays_zero(self):
        cpu, _ = run_program([".ORG 0", "ADDI $zero, $zero, 5", "HALT"])
        self.assertEqual(cpu.registers[0], 0)

    def test_signed_compare(self):
        cpu, _ = run_program([".ORG 0", "ADDI $t0, $zero, -1", "SLT $v0, $t0, $zero",
                              "SLTU $v1, $t0, $zero", "HALT"])
        self.assertEqual(cpu.registers[2], 1)   # -1 < 0 as signed numbers
        self.assertEqual(cpu.registers[3], 0)   # 0xFFFFFFFF < 0 as unsigned numbers → no

    def test_errors_are_clear(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            preprocess(["BEQ $t0 $zero nowhere"])
        with self.assertRaisesRegex(ValueError, "unknown instruction"):
            Instruction("MUL $t0 $t1 $t2")          # no multiply instruction (as required)
        with self.assertRaisesRegex(ValueError, "unknown register"):
            Instruction("ADD $t0 $t1 $xyz")


if __name__ == "__main__":
    unittest.main()
