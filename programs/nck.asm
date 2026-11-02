# ============================================================================
# nck.asm  —  compute nCk (number of ways to choose k items from n) without multiply or divide
# ★ This whole program was written by our group
#
# Why not use the formula n! / ((n-k)! × k!) on top of factorial.asm?
#   Because factorial grows very fast: 13! = 6,227,020,800 is already larger than a
#   32-bit register can hold (run factorial.asm with n = 13 to see the OVERFLOW warning).
#   But the instructor wants nCk up to n = 26 (nCkbound.py, Oct 13) → we need a method
#   whose numbers do not grow too large.
#
# Method used: Pascal's triangle
#   each number = the sum of the 2 numbers above it   C(i, j) = C(i-1, j-1) + C(i-1, j)
#               1                 ← row 0
#              1 1                ← row 1
#             1 2 1               ← row 2
#            1 3 3 1              ← row 3
#           1 4 6 4 1             ← row 4   e.g. 4C2 = 6
#   Only "addition" is used → intermediate numbers are never larger than the answer
#   → no overflow up to n = 33
#
# The current row is stored in memory as an array (using SW / LW)
#   row[j] is at address  ROW_BASE + 4 × j      (ROW_BASE = 0x4000, 4 bytes per slot)
#   The same row is updated over and over from "right to left"
#   (going left to right would change row[j-1] before it is used)
#
# Equivalent Python:
#     row = [1] + [0] * k
#     for i in range(1, n+1):
#         for j in range(min(i, k), 0, -1):
#             row[j] = row[j] + row[j-1]
#     return row[k]
#
# How to run (inside the sim folder):  python main.py ../programs/nck.asm
#   then type  n k  e.g.  5 2  → 10        26 13 → 10400600
#   To see the array in memory at the end, add  --mem 0x4000
# ============================================================================

.ORG 0

# ---------------------------------------------------------------------------
# main: read n and k → call nck(n, k) → print the result → exit
# ---------------------------------------------------------------------------
main:
    ORI   $v0, $zero, 5         # service 5 = read a number
    SYSCALL
    ADD   $s0, $v0, $zero       # $s0 = n
    ORI   $v0, $zero, 5
    SYSCALL
    ADD   $a1, $v0, $zero       # $a1 = k
    ADD   $a0, $s0, $zero       # $a0 = n

    JAL   nck                   # $v0 = nCk

    ADD   $a0, $v0, $zero       # print the result
    ORI   $v0, $zero, 1
    SYSCALL
    ORI   $a0, $zero, 10        # new line
    ORI   $v0, $zero, 11
    SYSCALL
    ORI   $v0, $zero, 10        # exit the program
    SYSCALL

# ---------------------------------------------------------------------------
# nck(n, k)
#   input : $a0 = n, $a1 = k
#   output: $v0 = nCk   (k < 0 or k > n gives 0, by mathematical definition)
#
#   variables:  $t9 = ROW_BASE (start address of the array)
#               $t4 = i (row)     $t2 = j (column)     $t3 = address of row[j]
#   This is a leaf function using only $t registers → no stack needed
# ---------------------------------------------------------------------------
nck:
    SLT   $t0, $a1, $zero       # k < 0 ?
    BNE   $t0, $zero, nck_zero
    SLT   $t0, $a0, $a1         # n < k ?
    BNE   $t0, $zero, nck_zero

    ORI   $t9, $zero, 0x4000    # $t9 = ROW_BASE

    # ---- set up the array: row[0] = 1, row[1..k] = 0 ----
    ORI   $t1, $zero, 1
    SW    $t1, 0($t9)           # row[0] = 1
    ORI   $t2, $zero, 1         # j = 1
init_loop:
    SLT   $t0, $a1, $t2         # k < j ?  (done up to k)
    BNE   $t0, $zero, init_done
    SLL   $t3, $t2, 2           # $t3 = j × 4   (shift left by 2 = ×4 → distance in bytes)
    ADD   $t3, $t3, $t9         # $t3 = address of row[j]
    SW    $zero, 0($t3)         # row[j] = 0
    ADDI  $t2, $t2, 1           # j = j + 1
    J     init_loop
init_done:

    # ---- build the triangle one row at a time, i = 1 .. n ----
    ORI   $t4, $zero, 1         # i = 1
row_loop:
    SLT   $t0, $a0, $t4         # n < i ?  (all rows done)
    BNE   $t0, $zero, row_done

    ADD   $t2, $t4, $zero       # j = i
    SLT   $t0, $a1, $t4         # k < i ?
    BEQ   $t0, $zero, col_loop
    ADD   $t2, $a1, $zero       # if so j = k   →  j = min(i, k)

col_loop:                       # loop j from right to left, down to 1
    BEQ   $t2, $zero, col_done
    SLL   $t3, $t2, 2           # address of row[j] = ROW_BASE + j × 4
    ADD   $t3, $t3, $t9
    LW    $t5, 0($t3)           # $t5 = row[j]
    LW    $t6, -4($t3)          # $t6 = row[j-1]   (previous slot, 4 bytes lower)
    ADD   $t5, $t5, $t6         # row[j] + row[j-1]   ← the only arithmetic in the algorithm
    SW    $t5, 0($t3)           # store back into row[j]
    ADDI  $t2, $t2, -1          # j = j - 1
    J     col_loop
col_done:
    ADDI  $t4, $t4, 1           # i = i + 1
    J     row_loop

row_done:
    SLL   $t3, $a1, 2           # the answer is in row[k]
    ADD   $t3, $t3, $t9
    LW    $v0, 0($t3)
    JR    $ra

nck_zero:                       # case where k is not in the range 0..n
    ADD   $v0, $zero, $zero
    JR    $ra
