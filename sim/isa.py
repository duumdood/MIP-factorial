# isa.py
# Handles instruction parsing and decoding
#
# ============================================================================
# ★ This file extends isa.py from the instructor's V7.1
#   Markers:  ★ [NEW]      = code added by our group
#             ★ [MODIFIED] = instructor's original code that we changed (with the reason)
#             no marker    = instructor's original code
#
#   Summary of changes:
#     1. preprocess()  : 2-pass assembler supporting labels (loop:), comments (#)
#                        and commas → assembly can be written the same way as in QtSpim
#                        (the instructor wrote in Readme V4: "should use the 2-pass technique")
#     2. reg2int()     : supports register names such as $t0 $sp $ra, not only $8
#                        (the instructor said on Sep 21: "shouldn't be hard, but I didn't do it")
#     3. imm2int()     : supports binary 0b... and negative hexadecimal numbers
#                        (the instructor wrote in Readme V4: "should also accept binary 0b")
#     4. decode2()     : prepares the operands of JR, SLL, SRL, SYSCALL that were left empty,
#                        and reports an error instead of exiting the program immediately
#     5. decode3()     : assembles R-type instructions into correct machine code
#                        (previously ADD/SUB/... became 00000000 because rs rt rd funct were missing)
#                        and places rs/rt of BEQ/BNE as in real MIPS
# ============================================================================

import re   # ★ [NEW] used to check the format of label names

allCMD=[
        ('ADD', 'R', '000000', '100000'),
        ('ADDI', 'I', '001000', '000000'),
        ('ADDIU', 'I', '001001', '000000'),
        ('ADDU', 'R', '000000', '100001'),
        ('AND', 'R', '000000', '100100'),
        ('ANDI', 'I', '001100', '000000'),
        ('BEQ', 'I', '000100', '000000'),
        ('BNE', 'I', '000101', '000000'),
        ('J', 'J', '000010', '000000'),
        ('JAL', 'J', '000011', '000000'),
        ('JR', 'R', '000000', '001000'),
        ('LBU', 'I', '100100', '000000'),
        ('LHU', 'I', '100101', '000000'),
        ('LL', 'I', '110000', '000000'),
        ('LUI', 'I', '001111', '000000'),
        ('LW', 'I', '100011', '000000'),
        ('NOR', 'R', '000000', '100111'),
        ('OR', 'R', '000000', '100101'),
        ('ORI', 'I', '001101', '000000'),
        ('SLT', 'R', '000000', '101010'),
        ('SLTI', 'I', '001010', '000000'),
        ('SLTIU', 'I', '001011', '000000'),
        ('SLTU', 'R', '000000', '101011'),
        ('SLL', 'R', '000000', '000000'),
        ('SRL', 'R', '000000', '000010'),
        ('SB', 'I', '101000', '000000'),
        ('SC', 'I', '111000', '000000'),
        ('SH', 'I', '101001', '000000'),
        ('SW', 'I', '101011', '000000'),
        ('SUB', 'R', '000000', '100010'),
        ('SUBU', 'R', '000000', '100011'),
        ]
# change allCMD to cmdDict
cmdDict={'ADD': ('ADD', 'R', '000000', '100000'), 'ADDI': ('ADDI', 'I', '001000', '000000'), 'ADDIU': ('ADDIU', 'I', '001001', '000000'), 'ADDU': ('ADDU', 'R', '000000', '100001'), 'AND': ('AND', 'R', '000000', '100100'), 'ANDI': ('ANDI', 'I', '001100', '000000'), 'BEQ': ('BEQ', 'I', '000100', '000000'), 'BNE': ('BNE', 'I', '000101', '000000'), 'J': ('J', 'J', '000010', '000000'), 'JAL': ('JAL', 'J', '000011', '000000'), 'JR': ('JR', 'R', '000000', '001000'), 'LBU': ('LBU', 'I', '100100', '000000'), 'LHU': ('LHU', 'I', '100101', '000000'), 'LL': ('LL', 'I', '110000', '000000'), 'LUI': ('LUI', 'I', '001111', '000000'), 'LW': ('LW', 'I', '100011', '000000'), 'NOR': ('NOR', 'R', '000000', '100111'), 'OR': ('OR', 'R', '000000', '100101'), 'ORI': ('ORI', 'I', '001101', '000000'), 'SLT': ('SLT', 'R', '000000', '101010'), 'SLTI': ('SLTI', 'I', '001010', '000000'), 'SLTIU': ('SLTIU', 'I', '001011', '000000'), 'SLTU': ('SLTU', 'R', '000000', '101011'), 'SLL': ('SLL', 'R', '000000', '000000'), 'SRL': ('SRL', 'R', '000000', '000010'), 'SB': ('SB', 'I', '101000', '000000'), 'SC': ('SC', 'I', '111000', '000000'), 'SH': ('SH', 'I', '101001', '000000'), 'SW': ('SW', 'I', '101011', '000000'), 'SUB': ('SUB', 'R', '000000', '100010'), 'SUBU': ('SUBU', 'R', '000000', '100011')}

# ★ [NEW] SYSCALL instruction (R-type, funct = 001100) for number input/output
#   Same convention as QtSpim: put the service number in $v0, then call SYSCALL
cmdDict['SYSCALL'] = ('SYSCALL', 'R', '000000', '001100')

# ★ [NEW] standard names of all 32 registers (position in the list = register number)
#   e.g. REG_NAMES[2] = 'v0' means $v0 is $2
REG_NAMES = ['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3',      # $0 - $7
             't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7',        # $8 - $15  temporaries
             's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',        # $16 - $23 saved registers
             't8', 't9', 'k0', 'k1', 'gp', 'sp', 'fp', 'ra']        # $24 - $31 ($sp = stack, $ra = return address)


# ★ [MODIFIED] imm2int: previously accepted only decimal, and hexadecimal starting with 0x
#   Added: binary (0b1010), negative hexadecimal (-0x10), uppercase (0XFF)
def imm2int(imm):
    """
    convert immediate in either hex or dec string to int
    """
    s = imm.strip().lower()
    negative = s.startswith('-')          # remember the sign first, then remove it
    if negative:
        s = s[1:]
    if s[:2] == '0x':                     # (original) hexadecimal
        value = int(s, 16)
    elif s[:2] == '0b':                   # ★ [NEW] binary
        value = int(s, 2)
    else:                                 # (original) decimal
        value = int(s)
    return -value if negative else value


# ★ [NEW] reg2int: convert a register name to its number 0-31
#   The instructor used int(x[1:]), which only works for "$8" (drop the $ and convert to a number)
#   Now every form is accepted:  "$8" → 8,  "$t0" → 8,  "$sp" → 29,  "R8" → 8 (as in the original example file)
def reg2int(token):
    name = token.strip().lstrip('$').lower()
    if name in REG_NAMES:                       # by name, e.g. t0, sp, ra
        number = REG_NAMES.index(name)
    elif name.isdigit():                        # by number, e.g. 8
        number = int(name)
    elif name[:1] == 'r' and name[1:].isdigit():  # R8 form (used by the original example file)
        number = int(name[1:])
    else:
        raise ValueError(f"unknown register '{token}'")
    if not 0 <= number <= 31:
        raise ValueError(f"register '{token}' must be between 0 and 31")
    return number


def reg2bin5(r):
    return ('0'*4+bin(r)[2:])[-5:]


# ★ [NEW] ================================================================
# preprocess: 2-pass assembler
#
# Original problem: branch offsets (BEQ/BNE) and jump addresses (J) had to be counted
#                   by hand, e.g. "BNE $0 $2 -3". Inserting one more line breaks
#                   every number in the program.
# Solution: write a name (label) instead, e.g. "BNE $0 $2 loop", and let the program
#           compute the number.
#
#   pass 1: read every line, remove comments and commas,
#           record "label → address" in a table (we can't know where a label further
#           down is until we have read the whole file)
#   pass 2: replace labels in instructions with numbers
#           - BEQ/BNE use a relative offset = (target address - address of next instruction) / 4
#           - J/JAL   use the actual target address
#
# The output is instruction lines in the instructor's original format → the original
# Instruction() class works unchanged. Old files that already use numbers (such as the
# instructor's instructions.txt) still work exactly as before.
# =======================================================================
LABEL_PATTERN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*$')   # label name: starts with a letter/underscore

# ★ [NEW] used by trace to show which line of the source file each instruction came from
def source_line_numbers(lines):
    """
    For each line that preprocess() keeps (.ORG and instructions), return its line number
    in the source file. Uses exactly the same rules as preprocess (comments, commas, labels),
    so instruction k (cpu.instructions[k]) came from source line numbers[k].
    """
    numbers = []
    for lineno, raw in enumerate(lines, 1):
        line = raw.split('#', 1)[0].replace(',', ' ').strip()
        while ':' in line:
            line = line.split(':', 1)[1].strip()
        if line:
            numbers.append(lineno)
    return numbers

def preprocess(lines):
    """
    lines  : list of text lines from the assembly file
    return : (instruction lines ready for Instruction, table of label → address)
    """
    labels = {}       # table of label → address
    cleaned = []      # (instruction text, address of the instruction, line number in the file)
    address = 0       # address of the next instruction (starts at 0 if there is no .ORG)

    # ---------------- pass 1 ----------------
    for lineno, raw in enumerate(lines, 1):
        line = raw.split('#', 1)[0]          # remove the comment (everything after #)
        line = line.replace(',', ' ').strip()  # commas → spaces (so "ADD $t0, $t1, $t2" works)

        while ':' in line:                   # label in front, e.g. "loop: ADD ..." or just "loop:"
            name, line = line.split(':', 1)
            name, line = name.strip(), line.strip()
            if not LABEL_PATTERN.match(name):
                raise ValueError(f"line {lineno}: invalid label name '{name}'")
            if name in labels:
                raise ValueError(f"line {lineno}: duplicate label '{name}'")
            labels[name] = address           # the label points to the address of the next instruction

        if not line:                         # empty line / comment only / label only
            continue

        if line.split()[0].upper() == '.ORG':
            if cleaned or labels:
                raise ValueError(f"line {lineno}: .ORG must come before all instructions and labels")
            address = imm2int(line.split()[1])   # change the starting address of the program
            cleaned.append((line, None, lineno))
            continue

        cleaned.append((line, address, lineno))
        address += 4                         # every MIPS instruction is 4 bytes long

    # ---------------- pass 2 ----------------
    output = []
    for line, addr, lineno in cleaned:
        parts = line.split()
        opcode = parts[0].upper()

        if opcode in ('BEQ', 'BNE') and len(parts) == 4:
            target = parts[3]
            if target in labels:
                parts[3] = str((labels[target] - (addr + 4)) // 4)
            elif LABEL_PATTERN.match(target):
                raise ValueError(f"line {lineno}: label '{target}' not found")

        elif opcode in ('J', 'JAL') and len(parts) == 2:
            target = parts[1]
            if target in labels:
                parts[1] = hex(labels[target])
            elif LABEL_PATTERN.match(target):
                raise ValueError(f"line {lineno}: label '{target}' not found")

        output.append(' '.join(parts))
    return output, labels
# ★ [END OF NEW CODE] ====================================================


class Instruction:
    def __init__(self, raw_line):
        """
        raw_line a single line from the instruction file
        Example: "ADD R1 R2 R3"
        """

        self.raw =  raw_line.strip()
        self.opcode = None
        self.operands = []
        self.hexcmd = None

        self.decode()
        self.decode2()
        self.decode3()
        #print(self.hexcmd, self.raw)

    def decode(self):
        """
        Split the instrucion into opcode and operands
        """

        if not self.raw:
            return

        parts = self.raw.replace(',', ' ').split()   # ★ [MODIFIED] added replace(',') to accept commas
        self.opcode = parts[0].upper()
        self.operands = parts[1:]

    # ★ [MODIFIED] all prepare... methods: changed int(x[1:]) to reg2int(x) to accept register names
    def prepareTypeR(self):
        self.operands[0] = reg2int(self.operands[0]) # Destination register
        self.operands[1] = reg2int(self.operands[1]) # First source register
        self.operands[2] = reg2int(self.operands[2]) # Second source register
        pass

    def prepareTypeI(self):
        self.operands[0] = reg2int(self.operands[0]) # Destination register
        self.operands[1] = reg2int(self.operands[1]) # First source register
        self.operands[2] = imm2int(self.operands[2])     # Immediate value
        pass

    def prepareLoadStore(self):
        self.operands[0] = reg2int(self.operands[0]) # Register conatainin the value to store

        offset_reg = self.operands[1] # Format: offset(rs)
        # ★ [MODIFIED] previously [1:-1] removed 1 character at each end, which only worked for "$21)";
        #   now "($sp)" and "($t0)" work, and a missing offset such as "($sp)" means offset = 0
        offset_text, base_text = offset_reg.split("(")
        self.operands[1] = reg2int(base_text.rstrip(')'))               # rs = base register
        self.operands.append(imm2int(offset_text) if offset_text else 0) # offset

    def prepareLoadUpper(self):
        self.operands[0] = reg2int(self.operands[0]) # Destination register
        self.operands[1] = imm2int(self.operands[1]) & 0xffff    # Immediate value

    def prepareTypeAddr(self):
        self.operands[0] = imm2int(self.operands[0])

    # ★ [NEW] SLL/SRL rd, rt, shamt  (shift bits: rd = rt << shamt or rt >> shamt)
    def prepareShift(self):
        self.operands[0] = reg2int(self.operands[0])   # rd
        self.operands[1] = reg2int(self.operands[1])   # rt
        self.operands[2] = imm2int(self.operands[2])   # shamt (number of bits to shift, 0-31)

    def decode2(self):
        """
        detect type of instruction and prepare rs rt rd immediate
        """
        # ★ [MODIFIED] wrapped in try so the user is told which line is wrong
        #   (previously a cryptic Python error was shown)
        try:
            match self.opcode:
                case 'ADD' | 'ADDU' | 'AND' | 'NOR' | 'OR' | 'SLT' | 'SLTU' | 'SUB' | 'SUBU' :
                    #print("Preparing R format")
                    self.prepareTypeR()
                case 'JR':
                    #print("Preparing R JR cmnd")
                    self.operands[0] = reg2int(self.operands[0])   # ★ [MODIFIED] previously pass (register not prepared)
                case 'SLL' | 'SRL' :
                    #print("Preparing R Shift cmnd")
                    self.prepareShift()                            # ★ [MODIFIED] previously pass
                case 'SYSCALL' :
                    pass                                           # ★ [NEW] no operands
                case 'ADDI' | 'ADDIU' | 'ANDI' | 'ORI' | 'SLTI' | 'SLTIU' | 'BEQ' | 'BNE':
                    #print("Preparing I format")
                    self.prepareTypeI()
                case 'LBU' | 'LHU' | 'LL' | 'LW' | 'SB' | 'SC' | 'SH' | 'SW' :
                    #print("Preparing I Load/Store cmnd")
                    self.prepareLoadStore()
                case 'LUI' :
                    #print("Preparing LUI cmnd")
                    self.prepareLoadUpper()
                    pass
                case 'J' | 'JAL' :
                    #print("Preparing J format")
                    self.prepareTypeAddr()
                case 'HALT' :
                    pass #print("HALT cmnd")
                case '.ORG' :
                    self.prepareTypeAddr()
                    pass #change PC
                case _:
                    # ★ [MODIFIED] previously print then exit(1), closing the program immediately
                    #   → now raises an error instead
                    raise ValueError(f"unknown instruction '{self.opcode}'")
        except (IndexError, ValueError) as e:
            raise ValueError(f"invalid instruction '{self.raw}': {e}") from None


    # ★ [MODIFIED] decode3 partly rewritten
    #   Original problem 1: R-type instructions (ADD, SUB, OR, ...) became 000000 followed by 26 zeros
    #                       because rs rt rd and funct were not filled in
    #                       (visible in the instructor's memory dump, where ADD is 00 00 00 00)
    #   Original problem 2: BEQ/BNE put the first operand in the rt field, but in real MIPS
    #                       "BEQ rs, rt, offset" the first operand is rs
    #
    #   MIPS 32-bit machine code formats:
    #     R-type: opcode(6) rs(5) rt(5) rd(5) shamt(5) funct(6)
    #     I-type: opcode(6) rs(5) rt(5) immediate(16)
    #     J-type: opcode(6) address(26)
    def decode3(self):
        """
        Assemble instruction to machine code (8 digit of hex in string)
        """
        opr = self.operands

        if self.opcode[0] != '.' and self.opcode != 'HALT':
            word = (cmdDict[self.opcode])[2]  # get 6bit bin opcode from dict
            funct = (cmdDict[self.opcode])[3] # ★ [NEW] last 6 bits of an R-type instruction

            if self.opcode in ['ADDI', 'ADDIU', 'ANDI', 'ORI', 'SLTI', 'SLTIU', 'LUI', 'SW' , 'LW']:
                if self.opcode == 'LUI':
                    rt,rs,imm = opr[0], 0, opr[1]
                else:
                    rt,rs,imm = opr[0], opr[1], opr[2]
                imm = imm & 0xffff            # ★ [MODIFIED] previously only negative numbers were converted; now always cut to 16 bits
                word += reg2bin5(rs) + reg2bin5(rt) + ('0'*15 + bin(imm)[2:])[-16:]
            elif self.opcode in ['BEQ', 'BNE']:
                # ★ [MODIFIED] first operand = rs, second operand = rt (as in real MIPS)
                rs, rt, imm = opr[0], opr[1], opr[2] & 0xffff
                word += reg2bin5(rs) + reg2bin5(rt) + ('0'*15 + bin(imm)[2:])[-16:]
            elif self.opcode in ['J', 'JAL']:
                addr = opr[0] >> 2
                word += ('0'*25 + bin(addr)[2:])[-26:]
            # ★ [NEW] ---- all R-type instructions ----
            elif self.opcode == 'JR':                       # JR rs : only the rs field is used
                word += reg2bin5(opr[0]) + '0'*15 + funct
            elif self.opcode == 'SYSCALL':                  # no operands
                word += '0'*20 + funct
            elif self.opcode in ['SLL', 'SRL']:             # rd, rt, shamt (rs = 0)
                rd, rt, shamt = opr[0], opr[1], opr[2]
                word += '00000' + reg2bin5(rt) + reg2bin5(rd) + reg2bin5(shamt) + funct
            elif cmdDict[self.opcode][1] == 'R':            # ADD SUB AND OR SLT ... : rd, rs, rt
                rd, rs, rt = opr[0], opr[1], opr[2]
                word += reg2bin5(rs) + reg2bin5(rt) + reg2bin5(rd) + '00000' + funct
            # ★ [END OF NEW CODE]
            else:
                word = word + '0'*26
            self.hexcmd =  (hex(int(('1' + word),2))[3:])


if  __name__ == "__main__":
    instructions = []
    with open("instructions.txt", "r") as file:
         instructions.extend([line.strip() for line in file if line.strip()])
    #print("\n".join(instructions))
    instructions, labels = preprocess(instructions)   # ★ [NEW] run the 2-pass assembler first
    instructions = [
            Instruction(line) for line in instructions
        ]
    for inst in instructions:
        # ★ [MODIFIED] removed the repeated inst.decode2() / inst.decode3() calls here,
        #   because the constructor already calls them; calling them again would convert
        #   operands that are already numbers a second time and raise an error
        if inst.opcode[0] != '.' and inst.opcode != 'HALT':
            print(inst.raw,'\t',inst.opcode, inst.operands, inst.hexcmd)
        else:
            print(inst.raw,'\t',inst.opcode, inst.operands, inst.hexcmd)
