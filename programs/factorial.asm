# ============================================================================
# factorial.asm  —  compute n!  without a multiply instruction (no MUL)
# ★ This whole program was written by our group
#
# Assignment (instructor, Sep 13): "write a factorial program and a python simulator
#   that runs it and outputs the result ... write your own multiply function if
#   there is no multiply instruction"
#
# Translated from the instructor's factorial_no_mul_1.py:
#     fac = 1
#     for i in range(2, n+1):
#         fac = mul(fac, i)        ← the inner loop (temp += fac) is moved into the mul function
#
# Structure: main → calls factorial → factorial calls mul many times
#
# How to run (inside the sim folder):  python main.py ../programs/factorial.asm
#   then type n, e.g. 5  → 120
#   Correct up to n = 12  (13! = 6,227,020,800 is larger than a 32-bit register can hold → OVERFLOW)
#
# Register usage conventions (standard MIPS):
#   $a0, $a1  = values passed into a function (arguments)
#   $v0       = value returned by a function / SYSCALL service number
#   $t0-$t9   = temporaries, a called function may overwrite them
#   $s0-$s7   = saved registers; a function that uses them must store the old values on
#               the stack first and restore them before returning
#   $sp       = stack pointer, points to the top of the stack
#   $ra       = return address (set automatically by JAL)
# ============================================================================

.ORG 0

# ---------------------------------------------------------------------------
# main: read n → call factorial(n) → print the result → exit
# ---------------------------------------------------------------------------
main:
    ORI   $v0, $zero, 5         # service 5 = read a number from the keyboard
    SYSCALL                     # $v0 = n typed by the user
    ADD   $a0, $v0, $zero       # pass n to the function in $a0

    JAL   factorial             # call factorial(n)  ($ra = address of the next line)
                                # after returning, the result is in $v0

    ADD   $a0, $v0, $zero       # move the result to $a0 to print it
    ORI   $v0, $zero, 1         # service 1 = print the number in $a0
    SYSCALL
    ORI   $a0, $zero, 10        # 10 = ASCII code for a new line
    ORI   $v0, $zero, 11        # service 11 = print a character
    SYSCALL
    ORI   $v0, $zero, 10        # service 10 = exit the program
    SYSCALL

# ---------------------------------------------------------------------------
# factorial(n)
#   input : $a0 = n
#   output: $v0 = n!     (n = 0 or 1 gives 1)
#
#   This function calls mul with JAL, which overwrites $ra,
#   so $ra must be saved on the stack first, otherwise we could not return to main.
#   $s0-$s2 used as variables are saved too (rule: give $s registers back unchanged)
#
#   stack after allocation (grows downward):
#       $sp+12 : old $ra
#       $sp+8  : old $s0
#       $sp+4  : old $s1
#       $sp+0  : old $s2   ← $sp points here
# ---------------------------------------------------------------------------
factorial:
    ADDI  $sp, $sp, -16         # allocate 4 slots × 4 bytes on the stack
    SW    $ra, 12($sp)          # save the return address
    SW    $s0, 8($sp)           # save the old values of $s0, $s1, $s2
    SW    $s1, 4($sp)
    SW    $s2, 0($sp)

    ADD   $s0, $a0, $zero       # $s0 = n
    ORI   $s1, $zero, 1         # $s1 = fac = 1
    ORI   $s2, $zero, 2         # $s2 = i   = 2

fact_loop:                      # for i in range(2, n+1):
    SLT   $t0, $s0, $s2         #   $t0 = 1 if n < i  (i has gone past n)
    BNE   $t0, $zero, fact_done #   if so → leave the loop

    ADD   $a0, $s1, $zero       #   argument 1 = fac
    ADD   $a1, $s2, $zero       #   argument 2 = i
    JAL   mul                   #   $v0 = fac × i
    ADD   $s1, $v0, $zero       #   fac = the product

    ADDI  $s2, $s2, 1           #   i = i + 1
    J     fact_loop             #   next iteration

fact_done:
    ADD   $v0, $s1, $zero       # return fac in $v0

    LW    $s2, 0($sp)           # restore the old values of $s2, $s1, $s0
    LW    $s1, 4($sp)
    LW    $s0, 8($sp)
    LW    $ra, 12($sp)          # get the saved return address back
    ADDI  $sp, $sp, 16          # free the stack space
    JR    $ra                   # return to the caller (main)

# ---------------------------------------------------------------------------
# mul(a, b)  —  "our own multiply function" replacing the MUL instruction
#   input : $a0 = a, $a1 = b   (b must not be negative)
#   output: $v0 = a × b
#   method: add a to itself b times   e.g. 6 × 4 = 6 + 6 + 6 + 6 = 24
#           (same as the inner loop "for j in range(i): temp += fac" of the instructor)
#
#   This is a leaf function (calls no other function) and uses only $t → no stack needed
# ---------------------------------------------------------------------------
mul:
    ADD   $v0, $zero, $zero     # result = 0
    ADD   $t0, $a1, $zero       # count  = b   (number of additions to do)

mul_loop:
    BEQ   $t0, $zero, mul_done  # all additions done (count = 0) → finish
    ADD   $v0, $v0, $a0         # result = result + a   ← OVERFLOW happens here if the result exceeds 32 bits
    ADDI  $t0, $t0, -1          # count = count - 1
    J     mul_loop

mul_done:
    JR    $ra                   # return to factorial
