# ============================================================================
# bigfactorial.asm  —  n! for LARGE n (e.g. 13!, 20!, 50!) without MUL or DIV
# ★ This whole program was written by our group
#
# Why a second factorial program?
#   factorial.asm keeps n! in ONE 32-bit register, so it is correct only up to 12!
#   (13! = 6,227,020,800 is larger than 2,147,483,647 → OVERFLOW).
#   Here n! is stored as an ARRAY OF DECIMAL DIGITS in memory, so the size of the
#   number is limited only by memory, not by the width of a register.
#
# Idea: multiply like on paper, one digit at a time, keeping a carry
#       e.g. 120 × 6:   0×6 + 0  = 0   → digit 0, carry 0
#                       2×6 + 0  = 12  → digit 2, carry 1
#                       1×6 + 1  = 7   → digit 7, carry 0      → 720
#
#   digit[j] is at address  DIGITS + 4 × j    (DIGITS = 0x4000, like the array in nck.asm)
#   digit[0] = ones, digit[1] = tens, ...  (stored "backwards", so the number can grow
#   at the end of the array when the carry is left over)
#
# Equivalent Python:
#     digits = [1]                       # the number 1
#     for i in range(2, n+1):
#         carry = 0
#         for j in range(len(digits)):
#             x = digits[j] * i + carry  # mul (our own multiply function)
#             digits[j] = x % 10         # divmod10 (repeated subtraction, no DIV)
#             carry     = x // 10
#         while carry > 0:               # the number got longer
#             digits.append(carry % 10)
#             carry //= 10
#     print the digits from the last one down to digits[0]
#
# Only ADD/SUB-type instructions are used: multiply = repeated addition (mul),
# divide by 10 = repeated subtraction (divmod10).
#
# How to run (inside the sim folder):  python main.py ../programs/bigfactorial.asm
#   then type n, e.g. 25  → 15511210043330985984000000
#   To see the digit array at the end, add  --mem 0x4000
#   Tested correct for every n from 0 to 60, and for 100.
#   The simulator stops after 1,000,000 instructions by default (protection against
#   infinite loops); that is enough up to 92! (968,851 instructions).
#   For larger n raise the limit, e.g. 100! needs about 1.3 million:
#       python main.py ../programs/bigfactorial.asm --max-steps 5000000
#
# Registers used by main:
#   $s0 = n         $s1 = len (number of digits)   $s2 = i (current multiplier)
#   $s3 = j (digit index)    $s4 = carry    $s5 = DIGITS (0x4000)    $s6 = address of digit[j]
#   main never returns (it ends with SYSCALL 10), so it does not need to save $s or $ra
# ============================================================================

.ORG 0

main:
    ORI   $v0, $zero, 5         # service 5 = read a number
    SYSCALL
    ADD   $s0, $v0, $zero       # $s0 = n

    ORI   $s5, $zero, 0x4000    # $s5 = DIGITS (start of the digit array)
    ORI   $t2, $zero, 1
    SW    $t2, 0($s5)           # digit[0] = 1   → the number starts as 1
    ORI   $s1, $zero, 1         # len = 1
    ORI   $s2, $zero, 2         # i = 2

# ---- for i = 2 .. n : number = number × i ----
i_loop:
    SLT   $t2, $s0, $s2         # n < i ?  (all multipliers done)
    BNE   $t2, $zero, print
    ADD   $s4, $zero, $zero     # carry = 0
    ADD   $s3, $zero, $zero     # j = 0

# ---- multiply every digit by i (ones digit first) ----
j_loop:
    SLT   $t2, $s3, $s1         # j < len ?
    BEQ   $t2, $zero, grow
    SLL   $s6, $s3, 2           # j × 4  (4 bytes per slot)
    ADD   $s6, $s6, $s5         # $s6 = address of digit[j]

    ADD   $a0, $s2, $zero       # a = i
    LW    $a1, 0($s6)           # b = digit[j]  (0..9, so mul adds at most 9 times)
    JAL   mul                   # $v0 = i × digit[j]
    ADD   $a0, $v0, $s4         # x = i × digit[j] + carry
    JAL   divmod10              # $v0 = x div 10,  $v1 = x mod 10
    SW    $v1, 0($s6)           # digit[j] = x mod 10
    ADD   $s4, $v0, $zero       # carry    = x div 10

    ADDI  $s3, $s3, 1           # j = j + 1
    J     j_loop

# ---- a carry is left over → the number gets more digits ----
grow:
    BEQ   $s4, $zero, next_i    # no carry left → done with this i
    SLL   $s6, $s1, 2
    ADD   $s6, $s6, $s5         # $s6 = address of digit[len]
    ADD   $a0, $s4, $zero
    JAL   divmod10
    SW    $v1, 0($s6)           # digit[len] = carry mod 10
    ADD   $s4, $v0, $zero       # carry = carry div 10
    ADDI  $s1, $s1, 1           # len = len + 1
    J     grow

next_i:
    ADDI  $s2, $s2, 1           # i = i + 1
    J     i_loop

# ---- print the digits, most significant first ----
print:
    ADDI  $s3, $s1, -1          # j = len - 1
print_loop:
    SLT   $t2, $s3, $zero       # j < 0 ?  (all digits printed)
    BNE   $t2, $zero, print_done
    SLL   $s6, $s3, 2
    ADD   $s6, $s6, $s5
    LW    $a0, 0($s6)           # $a0 = digit[j]
    ORI   $v0, $zero, 1         # service 1 = print the number in $a0 (one digit)
    SYSCALL
    ADDI  $s3, $s3, -1          # j = j - 1
    J     print_loop

print_done:
    ORI   $a0, $zero, 10        # new line
    ORI   $v0, $zero, 11
    SYSCALL
    ORI   $v0, $zero, 10        # exit the program
    SYSCALL

# ---------------------------------------------------------------------------
# mul(a, b)  —  the same "own multiply function" as in factorial.asm
#   input : $a0 = a, $a1 = b  (b >= 0)      output: $v0 = a × b
#   add a to itself b times; leaf function, uses only $t0 → no stack needed
# ---------------------------------------------------------------------------
mul:
    ADD   $v0, $zero, $zero     # result = 0
    ADD   $t0, $a1, $zero       # count  = b
mul_loop:
    BEQ   $t0, $zero, mul_done
    ADD   $v0, $v0, $a0         # result = result + a
    ADDI  $t0, $t0, -1          # count = count - 1
    J     mul_loop
mul_done:
    JR    $ra

# ---------------------------------------------------------------------------
# divmod10(x)  —  divide by 10 without a DIV instruction
#   input : $a0 = x (x >= 0)
#   output: $v0 = x div 10 (quotient),  $v1 = x mod 10 (remainder)
#   method: subtract 10 until less than 10 is left, counting the subtractions
#           e.g. 37 → 27 → 17 → 7   (3 subtractions) → quotient 3, remainder 7
#   x is small here (less than 10 × i), so the loop is short
#   leaf function, uses only $t1 → no stack needed
# ---------------------------------------------------------------------------
divmod10:
    ADD   $v0, $zero, $zero     # quotient  = 0
    ADD   $v1, $a0, $zero       # remainder = x
dm_loop:
    SLTI  $t1, $v1, 10          # remainder < 10 ?
    BNE   $t1, $zero, dm_done
    ADDI  $v1, $v1, -10         # remainder = remainder - 10
    ADDI  $v0, $v0, 1           # quotient  = quotient + 1
    J     dm_loop
dm_done:
    JR    $ra
