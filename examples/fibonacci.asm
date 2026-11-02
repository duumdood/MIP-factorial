# Fibonacci example for this project's MIPS simulator.
# Change 10 to another non-negative value to calculate F(n).
# F(0)=0, F(1)=1, F(10)=55.
.ORG 0
ORI $t0, $zero, 0       # a = F(0)
ORI $t1, $zero, 1       # b = F(1)
ORI $t2, $zero, 10      # n = 10

loop:
BEQ $t2, $zero, done
ADD $t3, $t0, $t1       # next = a + b
ADD $t0, $t1, $zero     # a = b
ADD $t1, $t3, $zero     # b = next
ADDI $t2, $t2, -1      # n -= 1
J loop

done:
ADD $a0, $t0, $zero   # print F(n)
ORI $v0, $zero, 1
SYSCALL
ORI $a0, $zero, 10    # newline character
ORI $v0, $zero, 11
SYSCALL
ORI $v0, $zero, 10    # exit
SYSCALL
