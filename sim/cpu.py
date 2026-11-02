#cpu.py
#simulates a simple CPU
#
# ============================================================================
# ★ This file extends cpu.py from the instructor's V7.1
#   Markers:  ★ [NEW]      = code added by our group
#             ★ [MODIFIED] = instructor's original code that we changed (with the reason)
#             no marker    = instructor's original code
#
#   How the CPU works (instructor's original design):
#     run() loops fetch → execute one instruction at a time.
#     self.PC holds "address ÷ 4" (e.g. PC = 3 means address 0x0C),
#     because each program line is stored in one list slot, but a real instruction is 4 bytes.
#
#   Summary of changes:
#     1. Added instructions that execute() could not run yet: SUB SUBU ADDU AND OR NOR SLT SLTU
#        ANDI SLL SRL JAL JR SYSCALL   (previously these did nothing and reported no error)
#     2. JAL / JR + stack pointer ($sp) → functions can be called (suggested by the instructor on Sep 21)
#     3. SYSCALL 1/5/10/11 → read numbers from the keyboard and print output (like QtSpim)
#     4. Detect OVERFLOW of ADD/ADDI/SUB and warn which instruction caused it
#        (validate() had a "too large" warning, but with a bug: int(...) was missing base 16)
#     5. Registers always hold 32-bit values (previously some instructions stored negative
#        numbers and some stored values larger than 32 bits)
#     6. SW/LW read/write 4 bytes as in real MIPS (previously the whole value went into one address)
#     7. Display modes: trace (one line per instruction) and step (press a key per instruction,
#        like T in Z80Sim)
#        (the instructor wrote in Readme V7: "control cpu.execute one step at a time, like trace")
# ============================================================================

import sys                                   # ★ [NEW] used to print warnings to stderr
from isa import Instruction, preprocess, REG_NAMES   # ★ [MODIFIED] added preprocess, REG_NAMES

DISP_FORMAT = "HEX" # INT or HEX form

# ★ [NEW] ----------------------------------------------------------------
# Constants and helper functions for 32-bit numbers
#
# MIPS registers are 32 bits wide, but Python ints can grow without limit,
# so we must "cut" values to 32 bits ourselves, otherwise we would not behave like real hardware.
#
#   u32(x)    : view as an unsigned number, 0 to 4,294,967,295
#   s32(x)    : view as a signed number, -2,147,483,648 to 2,147,483,647
#               (bit 31 = 1 means negative, following two's complement)
#   sext16(x) : extend a 16-bit number to 32 bits while keeping its sign (sign extension)
#               e.g. 0xFFFF (16 bits) = -1   used for the immediates of ADDI, LW, SW
MASK32 = 0xFFFFFFFF
INT32_MIN, INT32_MAX = -2**31, 2**31 - 1
SP_INIT = 0x00008000        # initial value of $sp: the stack starts at 0x8000 and grows downward
MAX_WARNINGS = 3            # print detailed overflow warnings only for the first 3 (to keep the screen readable)

def u32(value):
    return value & MASK32

def s32(value):
    value &= MASK32
    return value - 2**32 if value & 0x80000000 else value

def sext16(imm):
    imm &= 0xFFFF
    return imm - 0x10000 if imm & 0x8000 else imm
# ★ [END OF NEW CODE] ----------------------------------------------------


class CPU:
    # ★ [MODIFIED] added parameters:
    #   show_listing : whether to print the address + machine code table before running
    #   input_func   : function used to read numbers (normally Python's input; tests pass a fake one)
    #   quiet        : True = print no extra text (only SYSCALL output), suitable for autolab
    def __init__(self, instructions, memory, show_listing=True, input_func=input, quiet=False):
        """
        instructions: list of instruction strings
        memory: Memory object
        """

        self.PC = 0
        self.BASE_PC = self.PC
        self.registers = [0] * 32
        self.memory = memory
        self.running = True

        # ★ [NEW] additional state variables
        self.registers[29] = SP_INIT  # $sp points to the top of the stack
        self.steps = 0                # number of instructions executed so far
        self.overflows = []           # record of every overflow
        self.output = []              # everything printed by SYSCALL (checked by the tests)
        self.input_func = input_func
        self.input_buffer = []        # numbers typed but not read yet (so "5 2" can be typed on one line)
        self.quiet = quiet
        self.verbose = False          # set by run()
        self.error = None             # error message if the program stopped because of an error

        # ★ [NEW] run the 2-pass assembler first (labels, comments, commas) — see isa.preprocess
        instructions, self.labels = preprocess(instructions)
        if not instructions:
            raise ValueError("no instructions found in the program")

        # Parse instructions into Instruction objects
        #   decode(); docode2(); decode3()
        # decode() split opcode and operands
        # decode2() prepare value of operands
        # decode3() convert instruction to hexcode
        self.instructions = [
            Instruction(line) for line in instructions
        ]

        # display all instruction hexcode and raw instruction
        # and copy all instruction to memory
        textpos = 0     # ★ [MODIFIED] this line was missing → a file without .ORG caused an error (textpos undefined)
        if self.instructions[0].opcode == '.ORG':
            textpos = self.instructions[0].operands[0]
        self.text_start = textpos     # ★ [NEW] remember the start address for the memory display
        for instrctn in self.instructions:
            # put hexcmd in to memory
            strPC = ('0'*7+hex(textpos)[2:])[-8:]
            if show_listing:          # ★ [MODIFIED] printing is now optional
                print(strPC, instrctn.hexcmd, instrctn.raw, end='\t')
            if instrctn.hexcmd != None:
                for i in range(4):
                    #print(int(instrctn.hexcmd[i*2:i*2+2],16), end=" ")
                    val = int(instrctn.hexcmd[i*2:i*2+2],16)
                    self.memory.write(textpos, val)
                    textpos += 1
            elif instrctn.opcode != '.ORG':
                # ★ [MODIFIED] HALT has no machine code (hexcmd = None) but still occupies 4 bytes;
                #   previously textpos did not move → instructions after HALT showed wrong addresses
                textpos += 4
            if show_listing:
                print()


    def fetch(self):
        """
        Fetch the next instruction using PC
        """

        if self.PC - self.BASE_PC >= len(self.instructions):
            self.running = False
            return None

        # ★ [NEW] jumping to an address below the start of the program
        #   (Python lists accept negative indexes and would silently pick an instruction from the end)
        if self.PC - self.BASE_PC < 0:
            self.stop_with_error(f"PC = 0x{self.pc2hex()} is outside the program")
            return None

        instr = self.instructions[self.PC - self.BASE_PC]

        return instr

    # ★ [MODIFIED] validate: previously used int(hex(...)[-8:]) without base 16 → crashed when a value exceeded 32 bits
    #   Now every instruction writes registers through set_reg(), which already cuts to 32 bits.
    #   The "value too large" warning moved to the add/subtract step (see check_overflow),
    #   which can tell exactly which instruction caused it.
    def validate(self):
        """
        Check is all status are valid
        """
        if self.registers[0] != 0:
            print("****************Warning: register 0 must alwasys be zero")
            self.registers[0] = 0
            #return 1  # zero change
        for i  in range(32):
            self.registers[i] = u32(self.registers[i])   # safety net: force every register to 32 bits

    def pc2hex(self):
        strpc = ('0'*7+hex(self.PC*4)[2:])[-8:]
        return strpc.upper()

    # ★ [NEW] ---------------------------------------------------------------
    def set_reg(self, number, value):
        """Write a value to a register, always cut to 32 bits (used instead of self.registers[x] = ...)"""
        self.registers[number] = u32(value)

    def check_overflow(self, instr, exact):
        """
        exact = the mathematically correct result (Python can compute it with no size limit)
        If exact is outside the range a signed 32-bit register can hold = overflow.
        Real MIPS: ADD/ADDI/SUB stop the program (exception) on overflow.
        Our simulator: warn and keep running, so we can see how the result goes wrong.
        """
        if INT32_MIN <= exact <= INT32_MAX:
            return
        stored = s32(exact)
        self.overflows.append((self.pc2hex(), instr.raw, exact, stored))
        if len(self.overflows) <= MAX_WARNINGS:
            print(f"*** OVERFLOW at {self.pc2hex()}  {instr.raw}\n"
                  f"    correct value = {exact:,}  but a 32-bit register can only hold = {stored:,}",
                  file=sys.stderr)
        elif len(self.overflows) == MAX_WARNINGS + 1:
            print("*** (more overflows occurred, details no longer shown)", file=sys.stderr)

    def stop_with_error(self, message):
        self.error = message
        self.running = False
        print(f"*** ERROR: {message}", file=sys.stderr)

    def say(self, text):
        """Print extra text (not printed in quiet mode)"""
        if not self.quiet:
            print(text)
    # ★ [END OF NEW CODE] ---------------------------------------------------

    # ★ [MODIFIED] run: added display modes
    #   verbose   = the instructor's original style: print registers + memory after every instruction (very long)
    #   trace     = print one line per instruction, with the registers that changed
    #   step      = wait for Enter after every instruction (like the T command of Z80Sim)
    #   max_steps = protection against infinite loops
    def run(self, verbose=False, trace=False, step=False, max_steps=1_000_000):
        """
        Main fetch-decode-execute loop
        """
        self.verbose = verbose
        while self.running:
            if self.steps >= max_steps:                       # ★ [NEW]
                self.stop_with_error(f"more than {max_steps:,} instructions executed (possible infinite loop)")
                break
            instr = self.fetch()
            # instr.decode() #skip this since perform in constructor


            if instr is None:
                break
            before = self.registers.copy()                    # ★ [NEW] keep the old values to compare in trace
            pc_text = self.pc2hex()
            if verbose:
                print(f"Executed: {self.pc2hex()} {instr.raw}")
            self.execute(instr)


            # Debug output uncomment below
            if instr.opcode != '.ORG':
                if verbose:
                    self.debug()
                self.steps += 1                               # ★ [NEW]

            self.validate()
            if (trace or step) and instr.opcode != '.ORG':    # ★ [NEW]
                self.print_trace(pc_text, instr, before)
            self.PC += 1
            if step and self.running and instr.opcode != '.ORG':   # ★ [NEW]
                step = self.step_prompt()                     # returns False if the user pressed g (run to the end)
        # ★ [MODIFIED] "Last STATE" moved to main.py so main.py decides whether to show it
        #   (quiet mode for autolab must not mix in any other text)
        if len(self.overflows) > MAX_WARNINGS:
            print(f"*** {len(self.overflows)} overflows in total", file=sys.stderr)

    # ★ [NEW] ---------------------------------------------------------------
    def step_once(self):
        """
        Execute exactly ONE instruction (the same work as one pass of the loop in run()).
        Used by the TUI (tui.py), which needs to control the CPU one step at a time.
        Returns the executed instruction, or None if the program has finished.
        """
        if not self.running:
            return None
        instr = self.fetch()
        if instr is None:
            return None
        self.execute(instr)
        if instr.opcode != '.ORG':
            self.steps += 1
        self.validate()
        self.PC += 1
        return instr

    def current_index(self):
        """Index (in self.instructions) of the instruction that will run next"""
        return self.PC - self.BASE_PC

    def address_of(self, index):
        """Byte address of self.instructions[index] (the .ORG line itself has no address)"""
        has_org = self.instructions[0].opcode == '.ORG'
        return self.text_start + 4 * (index - (1 if has_org else 0))

    def print_trace(self, pc_text, instr, before):
        """Print 1 line: [address] instruction | registers that changed (old value -> new value)"""
        changes = []
        for i in range(32):
            if before[i] != self.registers[i]:
                changes.append(f"${REG_NAMES[i]}: {before[i]:08X} -> {self.registers[i]:08X}")
        print(f"[{pc_text}] {instr.raw:<26} | {', '.join(changes)}")

    def step_prompt(self):
        """
        Step mode: wait for a command from the user
          Enter = next instruction   r = show all registers   m = show memory
          g = run to the end         q = stop the program
        Returns True = stay in step mode, False = run to the end
        """
        while True:
            try:
                cmd = input("  [Enter]=next  r=registers  m=memory  g=run to end  q=quit > ").strip().lower()
            except (EOFError, KeyboardInterrupt):     # Ctrl+C / Ctrl+Z exits gracefully
                print()
                self.running = False
                return False
            if cmd == '':
                return True
            if cmd == 'r':
                self.print_registers()
            elif cmd.startswith('m'):
                # "m" = show the stack area, "m 0x4000" = show the given address
                parts = cmd.split()
                try:
                    start = int(parts[1], 0) if len(parts) > 1 else self.registers[29]
                except ValueError:
                    print("  usage: m  or  m 0x4000")
                    continue
                self.memory.dump(start, width=16, length=64)
            elif cmd == 'g':
                return False
            elif cmd == 'q':
                self.running = False
                return False

    def print_registers(self):
        """Show all 32 registers with their names, 4 per row"""
        for i in range(0, 32, 4):
            print("  " + "  ".join(f"${REG_NAMES[j]:<4}({j:>2})={self.registers[j]:08X}"
                                   for j in range(i, i + 4)))
    # ★ [END OF NEW CODE] ---------------------------------------------------

    def debug(self):
        """
        Show all register
        """
        W = 5
        print(f"Registers:")
        for i in range(len(self.registers)):
            if i%W==0: print(f"{i:>2}-{min(i+W-1, 31):>2}", end="")   # ★ [MODIFIED] the last row used to say 30-34 (registers only go up to 31)
            val = self.registers[i]
            if DISP_FORMAT == 'HEX':
                if val < 0: val = 2**32 + val
                hval = ('0'*7 + hex(val)[2:])[-8:]
                print(f"{hval:>11}",end="")
            else:
                print(f"{s32(val):>11}",end="")     # ★ [MODIFIED] show negative numbers correctly (registers hold 32-bit values)

            if i%W==W-1: print()
        print("\n"+"-" * 80)
        self.memory.dump(self.text_start)  #Start from first line of text   ★ [MODIFIED] use text_start (previously 4*(BASE_PC+1))
        print("-" * 80)

    def execute(self, instr):
        """
        Execute a single instruction
        """
        opcode = instr.opcode
        ops = instr.operands
        R = self.registers          # ★ [NEW] short alias to keep lines short

        # ★ [MODIFIED] ADD: previously added and stored directly, with no 32-bit cut and no overflow check
        #   Now: signed addition → check overflow → cut to 32 bits
        # ADD rd, rs, rt        # Adds the values in register rs and rt and stores the result in rd
        if opcode == "ADD":
            rd,rs,rt = ops[0], ops[1], ops[2]
            exact = s32(R[rs]) + s32(R[rt])
            self.check_overflow(instr, exact)
            self.set_reg(rd, exact)

        # ★ [NEW] ADDU rd, rs, rt : like ADD but no overflow check (U = unsigned / sign ignored)
        elif opcode == "ADDU":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, R[rs] + R[rt])

        # ★ [NEW] SUB rd, rs, rt : rd = rs - rt (overflow checked like ADD)
        elif opcode == "SUB":
            rd,rs,rt = ops[0], ops[1], ops[2]
            exact = s32(R[rs]) - s32(R[rt])
            self.check_overflow(instr, exact)
            self.set_reg(rd, exact)

        # ★ [NEW] SUBU rd, rs, rt : rd = rs - rt (no overflow check)
        elif opcode == "SUBU":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, R[rs] - R[rt])

        # ★ [NEW] AND / OR / NOR rd, rs, rt : bitwise operations
        elif opcode == "AND":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, R[rs] & R[rt])
        elif opcode == "OR":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, R[rs] | R[rt])
        elif opcode == "NOR":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, ~(R[rs] | R[rt]))

        # ★ [NEW] SLT rd, rs, rt : rd = 1 if rs < rt (signed comparison), otherwise 0
        #   used to build if / while conditions, e.g. "if i > n, leave the loop"
        elif opcode == "SLT":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, 1 if s32(R[rs]) < s32(R[rt]) else 0)

        # ★ [NEW] SLTU rd, rs, rt : like SLT but unsigned comparison
        elif opcode == "SLTU":
            rd,rs,rt = ops[0], ops[1], ops[2]
            self.set_reg(rd, 1 if R[rs] < R[rt] else 0)

        # ★ [MODIFIED] ADDI: added overflow check and 32-bit cut (immediate sign conversion follows the instructor's idea)
        # ADDI rt, rs, immediate # Adds an immediate value to the value in register rs and store the result in rt
        elif opcode == "ADDI":
            rt, rs, imm = ops[0], ops[1], ops[2]
            exact = s32(R[rs]) + sext16(imm)
            self.check_overflow(instr, exact)
            self.set_reg(rt, exact)

        # ★ [MODIFIED] ADDIU: real MIPS sign-extends the immediate just like ADDI;
        #   the only difference is no overflow check (previously imm was added as-is)
        # ADDIU rt, rs, immediate # Adds an immediate unsigned value to the value in register rs and store the result in rt
        elif opcode == "ADDIU":
            rt, rs, imm = ops[0], ops[1], ops[2]
            self.set_reg(rt, R[rs] + sext16(imm))

        # ★ [MODIFIED] SW: previously memory.write() put the whole value at one address;
        #   now writes 4 bytes (address to address+3) as in real MIPS
        # SW rt, offset(rs)     # Stores the value form register rt into memory at address (rs + offset)
        elif opcode == "SW":
            rt, rs, offset = ops[0], ops[1], ops[2]
            address = u32(R[rs] + sext16(offset))
            value = R[rt]
            self.memory.write_word(address, value)

        # LUI rt, immediate     # Loads an immediate into upper half of register rt
        elif opcode == "LUI":
            rt, imm = ops[0], ops[1]
            self.set_reg(rt, imm<<16)

        # ORI rt, immediate     # OR an immediate with lower half of register rt
        elif opcode == "ORI":
            rt, rs, imm = ops[0], ops[1], ops[2]
            self.set_reg(rt, R[rs] | (0xffff & imm))

        # ★ [NEW] ANDI rt, rs, immediate : AND with a 16-bit immediate (upper bits filled with 0)
        elif opcode == "ANDI":
            rt, rs, imm = ops[0], ops[1], ops[2]
            self.set_reg(rt, R[rs] & (0xffff & imm))

        # ★ [NEW] SLL rd, rt, shamt : shift bits left by shamt positions (= multiply by 2^shamt)
        #   used to compute array addresses, e.g. index × 4  (not a multiply instruction, just a bit shift)
        elif opcode == "SLL":
            rd, rt, shamt = ops[0], ops[1], ops[2]
            self.set_reg(rd, R[rt] << (shamt & 31))

        # ★ [NEW] SRL rd, rt, shamt : shift bits right (filling with 0 on the left)
        elif opcode == "SRL":
            rd, rt, shamt = ops[0], ops[1], ops[2]
            self.set_reg(rd, R[rt] >> (shamt & 31))

        # ★ [MODIFIED] LW: reads 4 bytes (matches the fixed SW)
        # LW rt, offset(rs)     # Loads a value from memroy at addres (rs + offset) into register rt
        elif opcode == "LW":
            rt, rs, offset = ops[0], ops[1], ops[2]
            address = u32(R[rs] + sext16(offset))
            self.set_reg(rt, self.memory.read_word(address))

        # ★ [MODIFIED] SLTI: previously wrote a negative value back into register rs while comparing
        #   (rs changed unintentionally); now the signed value is kept in a temporary, so rs is unchanged
        # SLTI rt, rs, immediate # Set if less than rt = rs<immediate? 1:0
        elif opcode == "SLTI":
            rt, rs, imm = ops[0], ops[1], ops[2]
            self.set_reg(rt, 1 if s32(R[rs]) < sext16(imm) else 0)

        # ★ [MODIFIED] SLTIU: real MIPS sign-extends the immediate to 32 bits first,
        #   then compares as unsigned numbers, e.g. imm = -1 → 0xFFFFFFFF (the largest value)
        #   (in Readme V6 the instructor wrote he was still unsure about this — we follow the MIPS manual)
        # SLTIU rt, rs, immediate # Set if less than rt = rs<immediate? 1:0
        elif opcode == "SLTIU":
            rt, rs, imm = ops[0], ops[1], ops[2]
            self.set_reg(rt, 1 if R[rs] < u32(sext16(imm)) else 0)

        # BEQ rs, rt, offset
        # If the values in registers rs and rt are equal,
        # branch to a new instruction by modifyin the PC
        elif opcode == "BEQ":
            rt, rs, offset = ops[0], ops[1], ops[2]

            # Compare registers and update PC if equal
            if self.registers[rs] == self.registers[rt]:
                self.PC += sext16(offset)       # ★ [MODIFIED] accept offsets written in hex, e.g. 0xfffd
                if self.verbose: print(f"BEQ check: R{rs}={self.registers[rs]} R{rt}={self.registers[rt]}")

        # BNE rs, rt, offset
        # If the values in registers rs and rt are not equal,
        # branch to a new instruction by modifyin the PC
        elif opcode == "BNE":
            rt, rs, offset = ops[0], ops[1], ops[2]

            # Compare registers and update PC if equal
            if self.registers[rs] != self.registers[rt]:
                self.PC += sext16(offset)       # ★ [MODIFIED] same as BEQ
                if self.verbose: print(f"BNE check: R{rs}={self.registers[rs]} R{rt}={self.registers[rt]}")

        # J address
        # branch to specific address by modifying the PC
        elif opcode == "J":
            target = ops[0]//4
            self.PC = target - 1 #step back 1 instruction since +1 in the loop run

        # ★ [NEW] JAL address : "Jump And Link" = call a function
        #   1) save the address of the next instruction (where to continue afterwards) in $ra ($31)
        #   2) jump to the function (like J)
        #   Example: the instruction is at 0x08 → $ra = 0x0C
        elif opcode == "JAL":
            self.set_reg(31, (self.PC + 1) * 4)   # PC holds address÷4, so multiply by 4 to get the byte address
            target = ops[0]//4
            self.PC = target - 1 #step back 1 instruction since +1 in the loop run

        # ★ [NEW] JR rs : "Jump Register" = jump to the address stored in a register
        #   used together with JAL: "JR $ra" = go back to where the function was called (return)
        elif opcode == "JR":
            rs = ops[0]
            self.PC = self.registers[rs]//4 - 1  #step back 1 instruction since +1 in the loop run

        # ★ [NEW] SYSCALL : ask the "system" to do input/output for us (same as QtSpim/MARS)
        #   put the service number in $v0 before calling
        #     $v0 = 1  : print the number in $a0
        #     $v0 = 5  : read a number from the keyboard → stored in $v0
        #     $v0 = 10 : end the program
        #     $v0 = 11 : print the character whose ASCII code is in $a0 (e.g. 10 = new line)
        elif opcode == "SYSCALL":
            service = self.registers[2]
            if service == 1:
                text = str(s32(self.registers[4]))
                self.output.append(text)
                print(text, end='', flush=True)
            elif service == 5:
                try:
                    while not self.input_buffer:      # wait until there is a number to read
                        prompt = "" if self.quiet else ">>> Enter a number and press Enter: "
                        self.input_buffer = self.input_func(prompt).split()
                    self.set_reg(2, int(self.input_buffer.pop(0), 0))
                except EOFError:
                    self.stop_with_error("no input (SYSCALL 5 needs a number)")
                except ValueError:
                    self.stop_with_error("input must be an integer")
            elif service == 10:
                self.running = False
            elif service == 11:
                char = chr(self.registers[4] & 0xFF)
                self.output.append(char)
                print(char, end='', flush=True)
            else:
                self.stop_with_error(f"unknown SYSCALL service {service}")

        # HALT
        # Stops CPU execution
        elif opcode  == "HALT":
            self.running = False

        # .ORG directive
        # Change PC to new value
        # Hope this line occur as first line of text part and using only one time
        elif opcode  == ".ORG":
            self.PC = ops[0]//4 - 1 #step back 1 instruction since +1 in the loop run
            self.BASE_PC = self.PC
            #self.running = False

        # ★ [NEW] instructions that can be assembled but have no execution yet (e.g. LBU, SB) → report clearly
        #   previously: silently skipped, giving wrong results that were hard to trace
        else:
            self.stop_with_error(f"execution of {opcode} is not supported yet")
