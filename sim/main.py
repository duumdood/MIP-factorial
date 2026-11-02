# main.py
# Entry point for the CPU simulator
#
# ============================================================================
# ★ This file extends main.py from the instructor's V7.1
#   Markers:  ★ [NEW] / ★ [MODIFIED] / no marker = instructor's original code
#
#   Before: only read a file named instructions.txt, with a single display style
#   ★ Now:  choose the program file and display mode from the command line
#
#   Usage (in Command Prompt, inside the sim folder):
#     python main.py                               run instructions.txt (as before)
#     python main.py ../programs/factorial.asm     run the given file
#     python main.py FILE -t                       trace: show every executed instruction, one per line
#     python main.py FILE -s                       step : press Enter for each instruction (like T in Z80Sim)
#     python main.py FILE -v                       verbose: the instructor's original output (registers+memory every instruction)
#     python main.py FILE -q                       quiet: show only SYSCALL output (for autolab)
#     python main.py FILE --mem 0x4000             show memory at this address at the end
#     python main.py FILE --int                    show registers as decimal numbers
#     python main.py FILE --tui                    full-screen view like Z80Sim in DOSBox (see tui.py)
# ============================================================================

import argparse                     # ★ [NEW] read options from the command line
import sys                          # ★ [NEW]
import cpu as cpu_module            # ★ [NEW] used to change DISP_FORMAT
from cpu import CPU
from memory import Memory

def load_instructions(filename):
    """
    Load instructions froma a text file.
    Each line is one instruction.
    """
    with open(filename, "r", encoding="utf-8") as file:   # ★ [MODIFIED] specify utf-8 so files open correctly on Windows
        return [line.rstrip('\n') for line in file]        # ★ [MODIFIED] keep every line (preprocess filters them and can report correct line numbers)

# ★ [NEW] command line options
def parse_args():
    parser = argparse.ArgumentParser(description="MIPS CPU simulator (extended from V7.1)")
    parser.add_argument("program", nargs="?", default="instructions.txt",
                        help="assembly program file (default: instructions.txt)")
    parser.add_argument("-t", "--trace", action="store_true", help="show every executed instruction")
    parser.add_argument("-s", "--step", action="store_true", help="run one instruction per Enter")
    parser.add_argument("-v", "--verbose", action="store_true", help="instructor's original output for every instruction")
    parser.add_argument("-q", "--quiet", action="store_true", help="show only SYSCALL output")
    parser.add_argument("--tui", action="store_true", help="full-screen view like Z80Sim in DOSBox")   # ★ [NEW]
    parser.add_argument("--int", action="store_true", help="show registers as decimal numbers")
    parser.add_argument("--mem", type=lambda x: int(x, 0), metavar="ADDR",
                        help="show memory at this address at the end, e.g. 0x4000")
    parser.add_argument("--max-steps", type=int, default=1_000_000,
                        help="maximum number of instructions, protects against infinite loops")
    return parser.parse_args()

def main():
    # ★ [NEW] allow special characters to be printed even when output is redirected to a file on Windows
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    args = parse_args()                                   # ★ [NEW]
    if args.int:
        cpu_module.DISP_FORMAT = "INT"

    # ★ [NEW] full-screen TUI mode (tui.py)
    if args.tui:
        try:
            from tui import run_tui
        except ImportError:
            print("*** The --tui mode needs the curses module. On Windows run once:  pip install windows-curses",
                  file=sys.stderr)
            sys.exit(1)
        try:
            run_tui(load_instructions(args.program), args.program)
        except (OSError, ValueError) as e:
            print(f"*** ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Load instruction from file
    try:                                                  # ★ [NEW] show readable error messages
        instructions = load_instructions(args.program)    # ★ [MODIFIED] the file name used to be fixed: "instructions.txt"

        #create memory
        memory = Memory()

        #create CPU
        cpu = CPU(instructions, memory, show_listing=not args.quiet, quiet=args.quiet)
    except (OSError, ValueError) as e:
        print(f"*** ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ★ [NEW] separator between the machine code table and the start of execution
    #   (makes it clear that the program has started running)
    if not args.quiet:
        print("=" * 80)
        print(f"Running program {args.program}")
        print("=" * 80)

    #run the CPU
    cpu.run(verbose=args.verbose, trace=args.trace, step=args.step,
            max_steps=args.max_steps)

    # ★ [MODIFIED] "Last STATE" used to be printed inside cpu.run(); moved here so it does not appear in quiet mode
    if not args.quiet:
        if cpu.output and not "".join(cpu.output).endswith("\n"):
            print()
        print("Last STATE")
        cpu.debug()
        if args.mem is not None:                          # ★ [NEW]
            print(f"Memory at 0x{args.mem:X}:")
            memory.dump(args.mem, width=16, length=64)
        print(f"Executed {cpu.steps:,} instructions", end="")   # ★ [NEW]
        if cpu.overflows:
            print(f"   WARNING: {len(cpu.overflows)} overflow(s), the result may be wrong", end="")
        print()
    if cpu.error:
        sys.exit(1)

# Only run main() if this file is excutec directly (not imported as a module)
if __name__ == "__main__":
    main()
