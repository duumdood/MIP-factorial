# gui.py
# ★ [NEW] This whole file was written by our group
#
# ============================================================================
# Window (GUI) version of the simulator, in the style of QtSpim / MARS.
# It only USES the existing simulator (cpu.py, isa.py, memory.py); nothing
# in those files was changed for it, and the command line (main.py) still works.
#
# Start it with:   python gui.py                        (empty editor)
#                  python gui.py ../programs/factorial.asm
# Tkinter comes with Python, so nothing has to be installed.
#
# Colours: dark "night mode" theme (see the colour constants below).
# Numbers: the HEX/DEC switch in the toolbar changes registers, memory words and the trace together.
#
# Window layout:
#   toolbar : Open, Save, Examples, Assemble, Step, Run/Pause, Reset, speed, HEX/DEC
#   left    : code editor with line numbers
#             - the line that will run NEXT is highlighted
#             - click a line number to set/remove a breakpoint (red dot)
#   right   : registers (changed ones highlighted in green) and memory
#   bottom  : tabs  Console (program output and warnings)
#                   Trace (every executed instruction; "Open in large window" pops it out)
#                   Machine code (address + machine code listing)
#
# How it drives the CPU:
#   Assemble  → builds a new CPU from the editor text (same as main.py)
#   Step      → cpu.step_once()  (one fetch → execute)
#   Run       → calls step_once() repeatedly with tkinter's after() timer,
#               so the window stays responsive; speed 10 = as fast as possible
#   SYSCALL 5 → the CPU calls ask_input(), which opens a pop-up input window and waits
# ============================================================================

import io
import sys
import tkinter as tk
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from cpu import CPU
from isa import Instruction, preprocess, REG_NAMES, source_line_numbers
from memory import Memory

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
# When packed into "MIPS Simulator.exe" (build_exe.bat), files bundled with the exe are unpacked
# to a temporary folder (sys._MEIPASS), and the exe sits in the project folder next to programs/.
if getattr(sys, "frozen", False):
    PROJECT = Path(sys.executable).resolve().parent
ICON_PNG = Path(getattr(sys, "_MEIPASS", HERE)) / "icon.png"
CODE_FONT = ("Consolas", 11)
UI_FONT = ("Segoe UI", 10)
MEM_ROWS, MEM_BYTES_PER_ROW = 16, 8
# speed 1..9 = delay in ms between instructions; speed 10 = no delay (run in batches)
SPEED_DELAY_MS = {1: 1000, 2: 600, 3: 400, 4: 250, 5: 150, 6: 80, 7: 40, 8: 15, 9: 3}
BATCH_SIZE = 5000                 # instructions per screen update at speed 10
MAX_STEPS = 1_000_000             # protection against infinite loops

# Dark ("night mode") colours: background and panels stay neutral; bright colours are used
# only for things to notice (current line, changed register, warning, error)
BG = "#0D1117"                    # window background (blue-black)
PANEL = "#161B22"                 # code / registers / memory / tabs
PANEL_2 = "#21262D"               # buttons, input boxes, selected tab
BORDER = "#30363D"                # thin lines between parts
FG = "#E6EDF3"                    # main text (soft white)
MUTED = "#8B949E"                 # secondary text, line numbers, comments
BLUE = "#58A6FF"                  # accent: instruction the CPU runs next, typed input
GREEN = "#3FB950"                 # register that just changed
ORANGE = "#F0B040"                # overflow / warnings
RED = "#F85149"                   # errors, breakpoints
CURRENT_BG = "#1C3354"            # background of the next instruction in the editor (dark blue)
CHANGED_BG = "#1B3D26"            # background of a changed register (dark green)
ERROR_BG = "#4A1D21"              # background of a line with an assembly error (dark red)
SELECT_BG = "#264F78"             # selected text


class InputCancelled(Exception):
    """Raised when the user resets or closes the window while the program waits for input"""


class SimulatorGUI(tk.Tk):
    def __init__(self, start_file=None):
        super().__init__()
        self.title("MIPS Simulator")
        try:                                       # window / taskbar icon
            self.icon_image = tk.PhotoImage(file=str(ICON_PNG))
            self.iconphoto(True, self.icon_image)
        except tk.TclError:
            pass
        self.geometry("1280x820")
        self.minsize(1000, 640)

        self.cpu = None               # created by assemble()
        self.memory = None
        self.line_of = []             # instruction index → editor line number
        self.breakpoints = set()      # editor line numbers
        self.changed = set()          # registers changed by the last instruction
        self.running = False          # True while Run is active
        self.dirty = True             # editor changed since the last assemble
        self.file_path = None
        self.input_var = tk.StringVar()
        self.waiting_for_input = False
        self.cancel_input = False
        self.closed = False           # True after the window is closed
        self.hex_mode = tk.BooleanVar(value=True)   # HEX/DEC switch in the toolbar: registers, memory and trace
        self.trace_records = []       # every traced instruction, kept so HEX/DEC can redraw the trace
        self.follow_sp = tk.BooleanVar(value=True)
        self.speed = tk.IntVar(value=6)

        self.apply_theme()
        self.build_toolbar()
        self.build_status_bar()       # packed BEFORE the body so a short window never hides it
        self.build_body()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind_all("<F5>", lambda e: self.toggle_run())
        self.bind_all("<F10>", lambda e: self.step())
        self.bind_all("<Control-s>", lambda e: self.save_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())

        if start_file:
            self.load_file(Path(start_file))
        self.refresh_all()

    # =================================================================== layout
    def build_toolbar(self):
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(bar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2)

        examples = ttk.Menubutton(bar, text="Examples")
        menu = tk.Menu(examples, tearoff=False)
        for path in self.example_files():
            menu.add_command(label=str(path.relative_to(PROJECT)), command=lambda p=path: self.load_file(p))
        examples["menu"] = menu
        examples.pack(side=tk.LEFT, padx=2)

        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(bar, text="Assemble", command=self.assemble).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Step (F10)", command=self.step).pack(side=tk.LEFT, padx=2)
        self.run_button = ttk.Button(bar, text="Run (F5)", command=self.toggle_run)
        self.run_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=2)

        ttk.Label(bar, text="Speed").pack(side=tk.LEFT, padx=(14, 4))
        ttk.Scale(bar, from_=1, to=10, variable=self.speed, length=110,
                  command=lambda v: self.speed.set(round(float(v)))).pack(side=tk.LEFT)
        self.speed_label = ttk.Label(bar, width=7)
        self.speed_label.pack(side=tk.LEFT, padx=4)
        self.speed.trace_add("write", lambda *a: self.show_speed())
        self.show_speed()

        # one switch for every number on screen (registers, memory words, trace)
        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Label(bar, text="Numbers").pack(side=tk.LEFT, padx=(0, 4))
        for text, value in (("HEX", True), ("DEC", False)):
            ttk.Radiobutton(bar, text=text, value=value, variable=self.hex_mode, style="Toggle.TRadiobutton",
                            command=self.on_number_format).pack(side=tk.LEFT)



    def build_body(self):
        vertical = ttk.PanedWindow(self, orient=tk.VERTICAL)
        vertical.pack(fill=tk.BOTH, expand=True, padx=6)
        top = ttk.PanedWindow(vertical, orient=tk.HORIZONTAL)
        vertical.add(top, weight=3)

        # ---- editor with line numbers ----
        editor_frame = ttk.Frame(top)
        top.add(editor_frame, weight=3)
        self.gutter = tk.Canvas(editor_frame, width=56, background=PANEL, highlightthickness=0)
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)
        scroll = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor = tk.Text(editor_frame, font=CODE_FONT, undo=True, wrap=tk.NONE,
                              yscrollcommand=lambda *a: (scroll.set(*a), self.draw_gutter()))
        self.style_text(self.editor)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.editor.yview)
        self.editor.tag_configure("current", background=CURRENT_BG)
        self.editor.tag_configure("error", background=ERROR_BG)
        self.editor.tag_configure("comment", foreground=MUTED)
        self.editor.tag_raise("sel")
        self.editor.bind("<<Modified>>", self.on_editor_modified)
        self.editor.bind("<Configure>", lambda e: self.draw_gutter())
        self.gutter.bind("<Button-1>", self.on_gutter_click)

        # ---- right side: registers + memory ----
        right = ttk.Frame(top, padding=(8, 0, 0, 0))
        top.add(right, weight=2)
        head = ttk.Frame(right)
        head.pack(fill=tk.X)
        ttk.Label(head, text="Registers", font=(UI_FONT[0], 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(head, text="green = just changed", style="Muted.TLabel").pack(side=tk.RIGHT)
        grid = ttk.Frame(right)
        grid.pack(fill=tk.X, pady=(4, 10))
        self.reg_labels = []
        for i in range(32):
            label = tk.Label(grid, font=CODE_FONT, anchor="w", padx=4, background=PANEL,
                             foreground=FG, relief=tk.FLAT, width=21)
            label.grid(row=i % 16, column=i // 16, sticky="we", padx=2, pady=0)
            self.reg_labels.append(label)

        mem_head = ttk.Frame(right)
        mem_head.pack(fill=tk.X)
        ttk.Label(mem_head, text="Memory", font=(UI_FONT[0], 10, "bold")).pack(side=tk.LEFT)
        ttk.Checkbutton(mem_head, text="Follow $sp", variable=self.follow_sp,
                        command=self.refresh_memory).pack(side=tk.RIGHT)
        self.mem_address = ttk.Entry(mem_head, width=12)
        self.mem_address.pack(side=tk.RIGHT, padx=4)
        self.mem_address.insert(0, "0x4000")
        self.mem_address.bind("<Return>", lambda e: (self.follow_sp.set(False), self.refresh_memory()))
        ttk.Label(mem_head, text="address").pack(side=tk.RIGHT)
        self.memory_view = tk.Text(right, font=CODE_FONT, height=MEM_ROWS, wrap=tk.NONE, relief=tk.FLAT)
        self.style_text(self.memory_view)
        self.memory_view.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.memory_view.tag_configure("sp", background=CHANGED_BG, foreground=GREEN)
        self.memory_view.tag_configure("head", foreground=MUTED)

        # ---- bottom tabs: console / trace / machine code ----
        tabs = ttk.Notebook(vertical)
        vertical.add(tabs, weight=1)
        console_tab = ttk.Frame(tabs)
        tabs.add(console_tab, text="Console")
        self.console = tk.Text(console_tab, font=CODE_FONT, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.style_text(self.console)
        self.console.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.console.tag_configure("error", foreground=RED)
        self.console.tag_configure("warning", foreground=ORANGE)
        self.console.tag_configure("info", foreground=MUTED)
        self.console.tag_configure("input", foreground=BLUE)

        self.trace_view = self.make_text_tab(tabs, "Trace", tools=[
            ("Open in large window", self.open_trace_window),
            ("Clear", self.clear_trace)])
        self.trace_popup = None               # the large trace window, when open
        self.listing_view = self.make_text_tab(tabs, "Machine code")
        self.tabs = tabs

    def make_text_tab(self, tabs, title, tools=()):
        frame = ttk.Frame(tabs)
        tabs.add(frame, text=title)
        if tools:                             # a row of buttons above the text
            row = ttk.Frame(frame)
            row.pack(side=tk.TOP, fill=tk.X, pady=2)
            for text, command in tools:
                ttk.Button(row, text=text, command=command).pack(side=tk.LEFT, padx=2)
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        view = tk.Text(frame, font=CODE_FONT, height=8, wrap=tk.NONE, state=tk.DISABLED,
                       yscrollcommand=scroll.set)
        self.style_text(view)
        view.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=view.yview)
        return view

    def build_status_bar(self):
        self.status = ttk.Label(self, anchor="w", padding=(8, 2))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ==================================================================== files
    def example_files(self):
        files = sorted((PROJECT / "programs").glob("*.asm")) + sorted((PROJECT / "examples").glob("*.txt"))
        return [p for p in files if p.is_file()]

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open assembly file", initialdir=PROJECT,
            filetypes=[("Assembly", "*.asm *.s *.txt"), ("All files", "*.*")])
        if path:
            self.load_file(Path(path))

    def load_file(self, path):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            messagebox.showerror("Open", f"Cannot open {path}:\n{e}")
            return
        self.stop_running()
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", text)
        self.editor.edit_reset()
        self.editor.edit_modified(False)          # loading a file is not an edit
        self.file_path = path
        self.title(f"MIPS Simulator — {path.name}")
        self.breakpoints.clear()
        self.cpu = None
        self.dirty = True
        self.color_comments()
        self.write_console(f"Opened {path}\n", "info")
        self.assemble()

    def save_file(self):
        if self.file_path is None:
            path = filedialog.asksaveasfilename(title="Save assembly file", initialdir=PROJECT,
                                                defaultextension=".asm",
                                                filetypes=[("Assembly", "*.asm"), ("All files", "*.*")])
            if not path:
                return
            self.file_path = Path(path)
        self.file_path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        self.title(f"MIPS Simulator — {self.file_path.name}")
        self.write_console(f"Saved {self.file_path}\n", "info")

    # ============================================================= assemble/run
    def assemble(self):
        """Translate the editor text and create a fresh CPU (like starting main.py)"""
        self.stop_running()
        self.cancel_pending_input()
        self.editor.tag_remove("error", "1.0", tk.END)
        lines = self.editor.get("1.0", "end-1c").split("\n")
        try:
            cleaned, _ = preprocess(lines)                        # errors here name their line
            numbers = source_line_numbers(lines)
            for index, text in enumerate(cleaned):                # find which line has a bad instruction
                try:
                    Instruction(text)
                except ValueError as e:
                    raise ValueError(f"line {numbers[index]}: {e}") from None
            self.memory = Memory()
            with redirect_stdout(io.StringIO()):
                self.cpu = CPU(lines, self.memory, show_listing=False,
                               input_func=self.ask_input, quiet=True)
        except ValueError as e:
            self.cpu = None
            self.write_console(f"Assemble error: {e}\n", "error")
            self.mark_error_line(str(e))
            self.set_status("Assemble error — fix the highlighted line")
            self.refresh_all()
            return False
        self.line_of = source_line_numbers(lines)
        self.dirty = False
        self.changed = set()
        self.clear_trace()
        if self.cpu.instructions[0].opcode == '.ORG':
            self.run_one(record=False)                            # run .ORG so PC shows the first real instruction
        self.fill_listing()
        self.write_console("Assembled. Press Step (F10) or Run (F5). "
                           "Click a line number to set a breakpoint.\n", "info")
        self.refresh_all()
        return True

    def ensure_ready(self):
        """Assemble first if there is no CPU yet or the code was edited"""
        if self.cpu is None or self.dirty:
            return self.assemble()
        return True

    def reset(self):
        self.assemble()

    def step(self):
        if self.running or not self.ensure_ready():
            return
        if not self.cpu.running:
            self.set_status("Program finished — press Reset to run again")
            return
        self.run_one()
        self.refresh_all()          # does nothing if the window was closed meanwhile

    def toggle_run(self):
        if self.running:
            self.stop_running()
            self.set_status("Paused")
            self.refresh_all()
            return
        if not self.ensure_ready():
            return
        if not self.cpu.running:
            self.set_status("Program finished — press Reset to run again")
            return
        self.running = True
        self.run_button.config(text="Pause (F5)")
        self.run_tick(first=True)

    def stop_running(self):
        self.running = False
        if hasattr(self, "run_button") and not self.closed:
            self.run_button.config(text="Run (F5)")

    def run_tick(self, first=False):
        """One timer tick of Run: one instruction (slow speeds) or a batch (speed 10)"""
        if not self.running or self.closed:
            return
        count = BATCH_SIZE if self.speed.get() >= 10 else 1
        for n in range(count):
            if not self.cpu.running or self.cpu.steps >= MAX_STEPS:
                break
            # stop at a breakpoint (but not on the line we are starting from)
            if not (first and n == 0) and self.current_line() in self.breakpoints:
                self.stop_running()
                self.set_status(f"Stopped at breakpoint, line {self.current_line()}")
                self.refresh_all()
                return
            self.run_one()
            if not self.running:              # input was cancelled
                break
        if self.closed:
            return
        if self.cpu.steps >= MAX_STEPS and self.cpu.running:
            self.write_console(f"Stopped after {MAX_STEPS:,} instructions (possible infinite loop)\n", "error")
            self.cpu.running = False
        if self.cpu.running and self.running:
            self.refresh_all()
            self.after(SPEED_DELAY_MS.get(self.speed.get(), 0), self.run_tick)
        else:
            self.stop_running()
            self.refresh_all()

    def run_one(self, record=True):
        """Run one instruction, collecting everything it printed"""
        before = self.cpu.registers.copy()
        pc_text = self.cpu.pc2hex()
        line = self.current_line()            # read before running: jumps change PC
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                instr = self.cpu.step_once()
        except InputCancelled:
            if not self.closed:
                self.stop_running()
            return None
        if out.getvalue():
            self.write_console(out.getvalue())
        if err.getvalue():
            text = err.getvalue()
            self.write_console(text, "warning" if "overflow" in text.lower() else "error")
        self.changed = {i for i in range(32) if before[i] != self.cpu.registers[i]}
        if record and instr is not None and instr.opcode != '.ORG':
            # keep the raw numbers, so the trace can be redrawn when HEX/DEC is switched
            entry = (line, pc_text, instr.raw,
                     [(i, before[i], self.cpu.registers[i]) for i in sorted(self.changed)])
            self.trace_records.append(entry)
            self.write_trace(self.format_trace(entry))
        if not self.cpu.running:
            self.finish_message()
        return instr

    def finish_message(self):
        if self.cpu.error:
            self.set_status(f"Error: {self.cpu.error}")
        else:
            note = f" — {len(self.cpu.overflows)} overflow(s), result may be wrong" if self.cpu.overflows else ""
            self.write_console(f"\nProgram finished after {self.cpu.steps:,} instructions{note}.\n", "info")
            self.set_status(f"Finished{note}")

    # ===================================================================== input
    def ask_input(self, prompt=""):
        """
        Called by the CPU for SYSCALL 5 (read a number).
        Opens a small input window in the middle of the simulator, so it is impossible to miss,
        and waits (keeping the main window alive) until the user presses OK or Stop.
        """
        self.cancel_input = False
        self.input_var.set("")
        self.waiting_for_input = True
        self.set_status("Program is waiting for input")
        self.refresh_all()
        self.open_input_dialog()

        # run_one() redirected stdout/stderr to collect program output; give the real ones back
        # while we wait, so nothing else that happens in the window is captured by mistake
        saved = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        try:
            self.wait_variable(self.input_var)      # runs the window until input_var changes
        finally:
            sys.stdout, sys.stderr = saved
        self.waiting_for_input = False
        self.close_input_dialog()
        if self.closed:
            raise InputCancelled()
        if self.cancel_input:
            self.write_console("Input cancelled - program paused. Press Step or Run to be asked again.\n", "info")
            self.set_status("Paused (input cancelled)")
            raise InputCancelled()
        value = self.input_var.get()
        self.write_console(f"input #{self.cpu.inputs_read}: {value}\n", "input")
        self.set_status("Running" if self.running else "Ready")
        return value

    def open_input_dialog(self):
        """The pop-up input window: a prompt, one text box, OK and Stop"""
        dialog = tk.Toplevel(self)
        self.input_dialog = dialog
        dialog.title("Input needed")
        dialog.configure(background=BG)
        dialog.transient(self)                     # stays on top of the simulator window
        dialog.resizable(False, False)
        dialog.protocol("WM_DELETE_WINDOW", self.cancel_pending_input)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)
        number = self.cpu.inputs_read if self.cpu else "?"
        ttk.Label(frame, text=f"The program asks for a number  (input #{number})",
                  font=(UI_FONT[0], 13, "bold")).pack(anchor="w")
        line = self.line_of[self.cpu.current_index()] if self.cpu and 0 <= self.cpu.current_index() < len(self.line_of) else "?"
        ttk.Label(frame, text=f"SYSCALL 5 at line {line}. Type an integer (several can be separated by spaces).",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 10))
        entry = tk.Entry(frame, font=(CODE_FONT[0], 16), width=24, relief=tk.SOLID, borderwidth=1,
                         background=PANEL_2, foreground=FG, insertbackground=BLUE,
                         highlightthickness=2, highlightcolor=BLUE, highlightbackground=BORDER)
        entry.pack(fill=tk.X)
        error = ttk.Label(frame, text="", foreground=RED)
        error.pack(anchor="w", pady=(4, 8))
        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)

        def submit(event=None):
            value = entry.get().strip()
            if not value:
                error.config(text="Enter a number first")
                return
            try:
                for token in value.split():
                    int(token, 0)                  # same rule the CPU uses: 12, -3, 0x1F
            except ValueError:
                error.config(text=f"'{token}' is not an integer")
                return
            self.input_var.set(value)

        entry.bind("<Return>", submit)
        entry.bind("<Key>", lambda e: error.config(text=""))
        dialog.bind("<Escape>", lambda e: self.cancel_pending_input())
        ttk.Button(buttons, text="Stop program", command=self.cancel_pending_input).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="OK", command=submit).pack(side=tk.RIGHT, padx=6)

        # centre it over the simulator window
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 3
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.lift()
        entry.focus_force()
        try:
            dialog.grab_set()                      # the main window waits until this one is answered
        except tk.TclError:
            pass

    def close_input_dialog(self):
        dialog = getattr(self, "input_dialog", None)
        self.input_dialog = None
        if dialog is not None:
            try:
                dialog.grab_release()
                dialog.destroy()
            except tk.TclError:
                pass

    def cancel_pending_input(self):
        if self.waiting_for_input:
            self.cancel_input = True
            self.input_var.set("cancel")

    def on_close(self):
        self.stop_running()
        self.closed = True
        self.cancel_pending_input()
        self.destroy()

    # =================================================================== display
    def refresh_all(self):
        if self.closed:
            return
        self.refresh_registers()
        self.refresh_memory()
        self.highlight_current_line()
        self.draw_gutter()
        if self.cpu is not None and not self.waiting_for_input:
            state = "finished" if not self.cpu.running else ("running" if self.running else "ready")
            self.status_right = f"PC = {self.cpu.pc2hex()}   steps = {self.cpu.steps:,}   {state}"
        else:
            self.status_right = ""
        self.update_status()

    def refresh_registers(self):
        values = self.cpu.registers if self.cpu else [0] * 32
        for i, label in enumerate(self.reg_labels):
            value = values[i]
            label.config(text=f"${REG_NAMES[i]:<4}({i:>2}) {self.number_text(value):>11}",
                         background=CHANGED_BG if i in self.changed else PANEL,
                         foreground=GREEN if i in self.changed else FG)

    def refresh_memory(self):
        view = self.memory_view
        view.config(state=tk.NORMAL)
        view.delete("1.0", tk.END)
        if self.cpu is None:
            view.config(state=tk.DISABLED)
            return
        sp = self.cpu.registers[29]
        if self.follow_sp.get():
            start = sp & ~(MEM_BYTES_PER_ROW - 1)
            self.mem_address.delete(0, tk.END)
            self.mem_address.insert(0, f"0x{start:X}")
        else:
            try:
                start = int(self.mem_address.get().strip(), 0) & ~(MEM_BYTES_PER_ROW - 1)
            except ValueError:
                start = 0
        hex_mode = self.hex_mode.get()
        # HEX: the raw bytes first, then each 4-byte word in hex
        # DEC: each 4-byte word as a signed decimal number FIRST (so it is visible even in a
        #      narrow panel), then the raw bytes. Example: 00 00 00 0A  →  10
        if hex_mode:
            view.insert(tk.END, f"{'address':<9} {'bytes (hex)':<24}   {'words (hex)':>20}\n", "head")
        else:
            view.insert(tk.END, f"{'address':<9} {'words (dec)':>23}   {'bytes (hex)':<24}\n", "head")
        for row in range(MEM_ROWS - 1):
            address = start + row * MEM_BYTES_PER_ROW
            values = [self.memory.read(address + b) & 0xFF for b in range(MEM_BYTES_PER_ROW)]
            text = " ".join(f"{v:02X}" for v in values[:4]) + "  " + " ".join(f"{v:02X}" for v in values[4:])
            words = "  ".join(f"{self.number_text(self.memory.read_word(address + w)):>11}" for w in (0, 4))
            marker = "  ◄ $sp" if address <= sp < address + MEM_BYTES_PER_ROW else ""
            body = f"{text}   {words}" if hex_mode else f"{words}   {text}"
            view.insert(tk.END, f"{address:08X}: {body}{marker}\n", "sp" if marker else ())
        view.config(state=tk.DISABLED)

    def current_line(self):
        """Editor line number of the instruction that will run next (None if none)"""
        if self.cpu is None or not self.cpu.running:
            return None
        index = self.cpu.current_index()
        return self.line_of[index] if 0 <= index < len(self.line_of) else None

    def highlight_current_line(self):
        self.editor.tag_remove("current", "1.0", tk.END)
        line = self.current_line()
        if line is not None and not self.dirty:
            self.editor.tag_add("current", f"{line}.0", f"{line}.0 lineend+1c")
            if not self.running or self.speed.get() < 10:
                self.editor.see(f"{line}.0")

    def mark_error_line(self, message):
        """Highlight the line named in an error such as 'line 12: ...'"""
        if message.startswith("line "):
            number = message[5:].split(":", 1)[0]
            if number.isdigit():
                self.editor.tag_add("error", f"{number}.0", f"{number}.0 lineend+1c")
                self.editor.see(f"{number}.0")

    def fill_listing(self):
        labels_at = {address: name for name, address in self.cpu.labels.items()}
        self.clear_view(self.listing_view)
        lines = ["Address   Code      Line  Label         Instruction\n"]
        for index, instr in enumerate(self.cpu.instructions):
            if instr.opcode == '.ORG':
                lines.append(f"{'':8}  {'':8}  {self.line_of[index]:>4}  {'':12}  {instr.raw}\n")
                continue
            address = self.cpu.address_of(index)
            label = labels_at.get(address, "")
            label = (label + ":") if label else ""
            lines.append(f"{address:08X}  {instr.hexcmd or '--------'}  {self.line_of[index]:>4}  "
                         f"{label:<12}  {instr.raw}\n")
        self.write_view(self.listing_view, "".join(lines))

    def draw_gutter(self):
        """Line numbers + breakpoint dots, drawn for the lines currently visible"""
        if not hasattr(self, "gutter"):
            return
        self.gutter.delete("all")
        index = self.editor.index("@0,0")
        while True:
            info = self.editor.dlineinfo(index)
            if info is None:
                break
            y = info[1]
            number = int(index.split(".")[0])
            if number in self.breakpoints:
                self.gutter.create_oval(6, y + 3, 18, y + 15, fill=RED, outline="")
            self.gutter.create_text(50, y + 1, anchor="ne", text=str(number),
                                    font=CODE_FONT, fill=MUTED)
            index = self.editor.index(f"{index}+1line")
            if self.editor.compare(index, ">=", "end"):
                break

    def on_gutter_click(self, event):
        index = self.editor.index(f"@0,{event.y}")
        number = int(index.split(".")[0])
        if number not in self.breakpoints and self.line_of and not self.dirty:
            # a blank/comment/label-only line never runs → put the breakpoint on the next instruction
            later = [n for n in self.line_of if n >= number]
            if later:
                number = later[0]
        if number in self.breakpoints:
            self.breakpoints.remove(number)
        else:
            self.breakpoints.add(number)
        self.draw_gutter()

    def on_editor_modified(self, event=None):
        if self.editor.edit_modified():
            self.dirty = True
            self.editor.edit_modified(False)
            self.editor.tag_remove("current", "1.0", tk.END)
            self.editor.tag_remove("error", "1.0", tk.END)
            self.color_comments()
            self.draw_gutter()

    def color_comments(self):
        self.editor.tag_remove("comment", "1.0", tk.END)
        start = "1.0"
        while True:
            start = self.editor.search("#", start, stopindex=tk.END)
            if not start:
                break
            self.editor.tag_add("comment", start, f"{start} lineend")
            start = f"{start} lineend"

    # ===================================================================== trace
    TRACE_HEADER = "line     [address ] instruction                | registers changed (old -> new)\n"

    def format_trace(self, entry):
        """One trace line; register values follow the HEX/DEC switch (addresses stay hex)"""
        line, pc_text, raw, changes = entry
        line_text = f"line {line:>3}" if line is not None else "line   ?"
        changed = ", ".join(f"${REG_NAMES[i]}: {self.number_text(old)} -> {self.number_text(new)}"
                            for i, old, new in changes)
        return f"{line_text} [{pc_text}] {raw:<26} | {changed}\n"

    def redraw_trace(self):
        """Rewrite the whole trace (used when HEX/DEC is switched)"""
        text = "".join(self.format_trace(entry) for entry in self.trace_records)
        for view, keep_header in ((self.trace_view, False),
                                  (getattr(self, "trace_popup_text", None) if self.trace_popup else None, True)):
            if view is None:
                continue
            view.config(state=tk.NORMAL)
            view.delete("2.0" if keep_header else "1.0", tk.END)
            if keep_header:
                view.insert(tk.END, "\n")
            view.insert(tk.END, text)
            view.see(tk.END)
            view.config(state=tk.DISABLED)

    def write_trace(self, text):
        """Add one line to the Trace tab, and to the large trace window if it is open"""
        self.write_view(self.trace_view, text)
        if self.trace_popup is not None:
            view = self.trace_popup_text
            view.config(state=tk.NORMAL)
            view.insert(tk.END, text)
            if self.trace_follow.get():
                view.see(tk.END)
            view.config(state=tk.DISABLED)

    def clear_trace(self):
        self.trace_records = []
        self.clear_view(self.trace_view)
        if self.trace_popup is not None:
            self.trace_popup_text.config(state=tk.NORMAL)
            self.trace_popup_text.delete("2.0", tk.END)          # keep the header line
            self.trace_popup_text.config(state=tk.DISABLED)

    def open_trace_window(self):
        """A large, resizable window showing the whole trace; it keeps updating while the program runs"""
        if self.trace_popup is not None:
            self.trace_popup.lift()
            return
        popup = tk.Toplevel(self)
        popup.title("Trace — every executed instruction")
        popup.geometry("1100x700")
        self.trace_popup = popup
        self.trace_follow = tk.BooleanVar(value=True)
        bar = ttk.Frame(popup, padding=(6, 4))
        bar.pack(side=tk.TOP, fill=tk.X)
        ttk.Checkbutton(bar, text="Follow newest line", variable=self.trace_follow).pack(side=tk.LEFT)
        ttk.Button(bar, text="Clear", command=self.clear_trace).pack(side=tk.LEFT, padx=8)
        ttk.Button(bar, text="Close", command=self.close_trace_window).pack(side=tk.RIGHT)
        yscroll = ttk.Scrollbar(popup, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll = ttk.Scrollbar(popup, orient=tk.HORIZONTAL)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        text = tk.Text(popup, font=(CODE_FONT[0], 12), wrap=tk.NONE,
                       yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        text.pack(fill=tk.BOTH, expand=True)
        yscroll.config(command=text.yview)
        xscroll.config(command=text.xview)
        self.style_text(text)
        popup.configure(background=BG)
        text.tag_configure("head", foreground=MUTED)
        text.insert(tk.END, self.TRACE_HEADER, "head")
        text.insert(tk.END, self.trace_view.get("1.0", "end-1c"))   # everything traced so far
        text.see(tk.END)
        text.config(state=tk.DISABLED)
        self.trace_popup_text = text
        popup.protocol("WM_DELETE_WINDOW", self.close_trace_window)

    def close_trace_window(self):
        if self.trace_popup is not None:
            self.trace_popup.destroy()
            self.trace_popup = None

    # ============================================================ number format
    def number_text(self, value):
        """A 32-bit value as text: 8 hex digits, or a signed decimal number (how MIPS sees it)"""
        value &= 0xFFFFFFFF
        if self.hex_mode.get():
            return f"{value:08X}"
        return str(value - 2**32 if value & 0x80000000 else value)

    def on_number_format(self):
        """HEX/DEC was switched: redraw everything that shows numbers"""
        self.refresh_registers()
        self.refresh_memory()
        self.redraw_trace()

    # ==================================================================== theme
    def apply_theme(self):
        """Dark colours for every ttk widget (buttons, tabs, scrollbars, ...)"""
        self.configure(background=BG)
        style = ttk.Style(self)
        style.theme_use("clam")                    # the built-in theme that allows custom colours
        style.configure(".", background=BG, foreground=FG, fieldbackground=PANEL_2,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                        troughcolor=PANEL, selectbackground=SELECT_BG, selectforeground=FG,
                        insertcolor=FG, font=UI_FONT)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("TButton", background=PANEL_2, foreground=FG, padding=(8, 3), width=-6)
        style.map("TButton", background=[("pressed", BORDER), ("active", BORDER)])
        style.configure("TMenubutton", background=PANEL_2, foreground=FG, padding=(8, 3), width=-8)
        style.map("TMenubutton", background=[("active", BORDER)])
        style.configure("TCheckbutton", background=BG, foreground=FG, indicatorbackground=PANEL_2,
                        indicatorforeground=BLUE)
        style.map("TCheckbutton", background=[("active", BG)],
                  indicatorbackground=[("selected", PANEL_2)])
        style.configure("Toggle.TRadiobutton", background=PANEL_2, foreground=MUTED,
                        padding=(8, 3), indicatorsize=0, indicatormargin=0, borderwidth=1)
        style.layout("Toggle.TRadiobutton",
                     [("Radiobutton.padding", {"sticky": "nswe",
                                               "children": [("Radiobutton.label", {"sticky": "nswe"})]})])
        style.map("Toggle.TRadiobutton", background=[("selected", BLUE), ("active", BORDER)],
                  foreground=[("selected", BG)])
        style.configure("TEntry", fieldbackground=PANEL_2, foreground=FG, insertcolor=FG)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(12, 4))
        style.map("TNotebook.Tab", background=[("selected", PANEL_2)], foreground=[("selected", FG)])
        style.configure("TPanedwindow", background=BORDER)
        style.configure("Sash", sashthickness=6, gripcount=0)
        for name in ("TScrollbar", "Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.configure(name, background=PANEL_2, troughcolor=PANEL, arrowcolor=MUTED,
                            bordercolor=BORDER, lightcolor=PANEL_2, darkcolor=PANEL_2)
            style.map(name, background=[("active", BORDER)])
        style.configure("Horizontal.TScale", background=BLUE, troughcolor=PANEL_2)
        style.configure("TSeparator", background=BORDER)
        self.option_add("*Menu.background", PANEL_2)
        self.option_add("*Menu.foreground", FG)
        self.option_add("*Menu.activeBackground", SELECT_BG)
        self.option_add("*Menu.activeForeground", FG)

    def style_text(self, view):
        """Dark colours for a tk.Text box"""
        view.configure(background=PANEL, foreground=FG, insertbackground=BLUE,
                       selectbackground=SELECT_BG, selectforeground=FG,
                       highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER,
                       borderwidth=0, padx=4, pady=2)

    # ===================================================================== helpers
    def write_console(self, text, tag=None):
        self.write_view(self.console, text, tag)

    def write_view(self, view, text, tag=None):
        if self.closed:
            return
        view.config(state=tk.NORMAL)
        view.insert(tk.END, text, tag or ())
        view.see(tk.END)
        view.config(state=tk.DISABLED)

    def clear_view(self, view):
        view.config(state=tk.NORMAL)
        view.delete("1.0", tk.END)
        view.config(state=tk.DISABLED)

    def show_speed(self):
        value = self.speed.get()
        self.speed_label.config(text="max" if value >= 10 else f"{value}/10")

    def set_status(self, text):
        self.status_left = text
        self.update_status()

    def update_status(self):
        left = getattr(self, "status_left", "")
        right = getattr(self, "status_right", "")
        self.status.config(text=f"{left}    {right}" if left else right)


def main(start=None):
    """start = assembly file to open (main.py --gui passes it; otherwise taken from the command line)"""
    if sys.platform == "win32":                 # sharp (not blurry) text on high-DPI Windows screens
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            # show our own icon in the taskbar instead of Python's
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MIPSSimulator.GUI")
        except (AttributeError, OSError):
            pass
    if start is None and len(sys.argv) > 1 and __name__ == "__main__":
        start = sys.argv[1]
    app = SimulatorGUI(start)
    app.mainloop()


if __name__ == "__main__":
    main()
