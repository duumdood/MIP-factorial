# tui.py
# ★ [NEW] This whole file was written by our group
#
# ============================================================================
# Text User Interface (TUI) for the simulator, in the style of Z80Sim under DOSBox
# (the simulator used in the Microprocessor Lab).
#
# Start it with:   python main.py ../programs/factorial.asm --tui
#
# Screen layout:
#   ┌ title bar: program name, PC, number of steps, status
#   │ Registers : all 32 registers with names; registers changed by the last
#   │             instruction are highlighted
#   │ Program   : address, machine code, instruction; the arrow ► marks the
#   │             instruction that will run NEXT
#   │ Memory    : 8 bytes per row; follows $sp by default (shows the stack)
#   │ Output    : what the program printed with SYSCALL
#   │ Message   : warnings (e.g. OVERFLOW) and input prompts
#   └ key help
#
# Keys:
#   T / Enter / Space : run one instruction (Trace)
#   G                 : run to the end (Go)
#   M                 : choose a memory address to view (empty = follow $sp)
#   Up / Down         : scroll the memory view
#   R                 : restart the program (Reset)
#   Q                 : quit
#
# On Windows, curses must be installed once:   pip install windows-curses
# ============================================================================

import curses
import io
from contextlib import redirect_stdout, redirect_stderr

from cpu import CPU
from isa import REG_NAMES
from memory import Memory

MIN_ROWS, MIN_COLS = 24, 90
MEM_BYTES_PER_ROW = 8
MAX_GO_STEPS = 1_000_000        # protection against infinite loops when pressing G


class SimulatorTUI:
    def __init__(self, screen, source_lines, program_name):
        self.screen = screen
        self.source_lines = source_lines
        self.program_name = program_name
        self.reset()

    # ---------------------------------------------------------------- state
    def reset(self):
        """(Re)create the CPU and memory, like pressing reset on a real board"""
        self.memory = Memory()
        with redirect_stdout(io.StringIO()):
            self.cpu = CPU(self.source_lines, self.memory, show_listing=False,
                           input_func=self.ask_input)
        self.output_text = ""            # everything printed by the program
        self.message = "Ready. Press T to run one instruction, G to run to the end."
        self.changed = set()             # registers changed by the last instruction
        self.mem_start = None            # None = follow $sp
        self.labels_at = {addr: name for name, addr in self.cpu.labels.items()}
        if self.cpu.instructions[0].opcode == '.ORG':
            self.run_one()               # execute .ORG right away so PC shows the first real instruction

    def run_one(self):
        """Run one instruction and collect everything it printed"""
        before = self.cpu.registers.copy()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            instr = self.cpu.step_once()
        self.output_text += out.getvalue()
        warning = err.getvalue().strip()
        if warning:
            self.message = " ".join(warning.split())       # e.g. the OVERFLOW warning
        self.changed = {i for i in range(32) if before[i] != self.cpu.registers[i]}
        if instr is None or not self.cpu.running:
            self.message = "Program finished. Press R to restart or Q to quit."
            if self.cpu.overflows:                         # keep the overflow visible at the end
                address, source, exact, stored = self.cpu.overflows[0]
                self.message = (f"Finished with {len(self.cpu.overflows)} OVERFLOW(s)! First at {address} "
                                f"{source}: correct {exact:,}, stored {stored:,}")
            if self.cpu.error:
                self.message = f"ERROR: {self.cpu.error}"
        return instr

    def run_to_end(self):
        self.message = "Running..."
        self.draw()
        count = 0
        while self.cpu.running and count < MAX_GO_STEPS:
            if self.run_one() is None:
                break
            count += 1
        if self.cpu.running:
            self.message = f"Stopped after {MAX_GO_STEPS:,} instructions (possible infinite loop)."

    def ask_input(self, prompt=""):
        """Called by SYSCALL 5: read a number on the message line"""
        rows, cols = self.screen.getmaxyx()
        self.draw()
        text = ">>> Program asks for input. Type a number and press Enter: "
        self.screen.move(rows - 2, 0)
        self.screen.clrtoeol()
        self.screen.addstr(rows - 2, 0, text[:cols - 12], curses.A_BOLD)
        curses.echo()
        curses.curs_set(1)
        try:
            value = self.screen.getstr(rows - 2, min(len(text), cols - 12), 20).decode(errors="ignore")
        finally:
            curses.noecho()
            curses.curs_set(0)
        self.output_text += value + "\n"            # echo the input into the output panel
        return value

    # --------------------------------------------------------------- drawing
    def put(self, row, col, text, attr=0):
        """Write text safely (never past the edge of the window)"""
        rows, cols = self.screen.getmaxyx()
        if 0 <= row < rows and col < cols - 1:
            self.screen.addstr(row, col, text[:cols - 1 - col], attr)

    def draw(self):
        scr = self.screen
        scr.erase()
        rows, cols = scr.getmaxyx()
        if rows < MIN_ROWS or cols < MIN_COLS:
            self.put(0, 0, f"Please make the window at least {MIN_COLS}x{MIN_ROWS} "
                           f"(now {cols}x{rows}). Q = quit")
            scr.refresh()
            return
        cpu = self.cpu
        status = "RUNNING" if cpu.running else ("ERROR" if cpu.error else "FINISHED")

        # ---- title bar ----
        title = (f" MIPS Simulator | {self.program_name} | PC={cpu.pc2hex()} "
                 f"| Steps={cpu.steps:,} | {status} ")
        self.put(0, 0, title.ljust(cols - 1), curses.A_REVERSE)

        # ---- registers: 8 rows x 4 columns ----
        for i in range(32):
            row, col = 1 + i // 4, (i % 4) * 22
            text = f"${REG_NAMES[i]:<4}({i:>2}) {cpu.registers[i]:08X}"
            attr = self.color(1) | curses.A_BOLD if i in self.changed else 0
            self.put(row, col + 1, text, attr)

        # ---- panel positions ----
        top = 10                              # first row of the program/memory panels
        bottom = rows - 6                     # last row of the program/memory panels
        height = bottom - top + 1
        mem_width = 10 + MEM_BYTES_PER_ROW * 3 + 8
        split = cols - mem_width - 2          # column where the memory panel starts

        mem_addr = self.memory_start()
        self.put(top - 1, 0, "─" * (cols - 1))
        self.put(top - 1, 2, " Program  (► = next instruction) ", curses.A_BOLD)
        self.put(top - 1, split + 1, f" Memory @ {mem_addr:08X} ", curses.A_BOLD)

        # ---- program listing, centred on the current instruction ----
        current = cpu.current_index()
        first = max(0, min(current - height // 2, len(cpu.instructions) - height))
        for line in range(height):
            index = first + line
            if index >= len(cpu.instructions):
                break
            instr = cpu.instructions[index]
            if instr.opcode == '.ORG':
                text = f"           {'':8}  {instr.raw}"
            else:
                address = cpu.address_of(index)
                label = self.labels_at.get(address, "")
                label = (label + ":")[:12] if label else ""
                text = f"  {address:08X} {instr.hexcmd or '--------'}  {label:<13}{instr.raw}"
            if index == current and cpu.running:
                self.put(top + line, 0, ("►" + text[1:]).ljust(split - 1)[:split - 1], self.color(2) | curses.A_BOLD)
            else:
                self.put(top + line, 0, text[:split - 1])

        # ---- memory panel ----
        sp = cpu.registers[29]
        for line in range(height):
            address = (mem_addr + line * MEM_BYTES_PER_ROW) & 0xFFFFFFFF
            values = [self.memory.read(address + b) & 0xFF for b in range(MEM_BYTES_PER_ROW)]
            groups = "  ".join(" ".join(f"{v:02X}" for v in values[g:g + 4])
                               for g in range(0, MEM_BYTES_PER_ROW, 4))
            marker = " ◄$sp" if address <= sp < address + MEM_BYTES_PER_ROW else ""
            self.put(top + line, split, "│")
            self.put(top + line, split + 1, f"{address:08X}: {groups}{marker}",
                     self.color(3) if marker else 0)

        # ---- output panel: last 2 lines printed by the program ----
        self.put(bottom + 1, 0, "─" * (cols - 1))
        self.put(bottom + 1, 2, " Output ", curses.A_BOLD)
        lines = self.output_text.split("\n")
        for k, text in enumerate(lines[-3:-1] if self.output_text.endswith("\n") else lines[-2:]):
            self.put(bottom + 2 + k, 1, text)

        # ---- message line and key help ----
        self.put(rows - 2, 0, self.message, self.color(1) | curses.A_BOLD)
        keys = " [T/Enter] Step  [G] Go  [M] Memory addr  [Up/Down] Scroll mem  [R] Reset  [Q] Quit "
        self.put(rows - 1, 0, keys.ljust(cols - 1), curses.A_REVERSE)
        scr.refresh()

    def memory_start(self):
        if self.mem_start is not None:
            return self.mem_start
        return self.cpu.registers[29] & ~(MEM_BYTES_PER_ROW - 1)   # follow $sp

    def color(self, pair):
        return curses.color_pair(pair) if curses.has_colors() else curses.A_BOLD

    # ------------------------------------------------------------ main loop
    def ask_memory_address(self):
        rows, cols = self.screen.getmaxyx()
        text = "Memory address (e.g. 0x4000, empty = follow $sp): "
        self.screen.move(rows - 2, 0)
        self.screen.clrtoeol()
        self.put(rows - 2, 0, text, curses.A_BOLD)
        curses.echo()
        curses.curs_set(1)
        try:
            value = self.screen.getstr(rows - 2, len(text), 16).decode(errors="ignore").strip()
        finally:
            curses.noecho()
            curses.curs_set(0)
        if not value:
            self.mem_start = None
            self.message = "Memory view follows $sp (the stack)."
            return
        try:
            self.mem_start = int(value, 0) & ~(MEM_BYTES_PER_ROW - 1)
            self.message = f"Memory view at 0x{self.mem_start:08X}."
        except ValueError:
            self.message = f"'{value}' is not a valid address."

    def loop(self):
        while True:
            self.draw()
            key = self.screen.getch()
            if key in (ord('q'), ord('Q')):
                return
            if key in (ord('t'), ord('T'), ord(' '), 10, 13, curses.KEY_ENTER):
                if self.cpu.running:
                    self.message = ""
                    self.run_one()
            elif key in (ord('g'), ord('G')):
                if self.cpu.running:
                    self.run_to_end()
            elif key in (ord('r'), ord('R')):
                self.reset()
            elif key in (ord('m'), ord('M')):
                self.ask_memory_address()
            elif key in (curses.KEY_UP, curses.KEY_DOWN):
                step = -MEM_BYTES_PER_ROW if key == curses.KEY_UP else MEM_BYTES_PER_ROW
                self.mem_start = max(0, self.memory_start() + step)


def run_tui(source_lines, program_name):
    """Entry point called by main.py"""
    def start(screen):
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()
            background = curses.COLOR_BLACK
            try:
                curses.use_default_colors()                # keep the terminal's own background
                background = -1
            except curses.error:
                pass
            curses.init_pair(1, curses.COLOR_YELLOW, background)        # changed registers / messages
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)  # current instruction
            curses.init_pair(3, curses.COLOR_GREEN, background)         # row where $sp points
        screen.keypad(True)
        SimulatorTUI(screen, source_lines, program_name).loop()
    curses.wrapper(start)
