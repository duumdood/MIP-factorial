# MIPS Simulator.pyw
# ★ [NEW] Double-click this file to open the simulator window.
#   On Windows, .pyw files run with pythonw.exe, so no black console window appears.
#   (The same as running:  cd sim  then  python gui.py)

import sys
from pathlib import Path

SIM = Path(__file__).resolve().parent / "sim"
sys.path.insert(0, str(SIM))

try:
    import gui
except SyntaxError:
    # isa.py uses "match", which needs Python 3.10 or newer; pythonw has no console to show errors
    import tkinter as tk
    from tkinter import messagebox
    tk.Tk().withdraw()
    messagebox.showerror("MIPS Simulator",
                         f"This program needs Python 3.10 or newer.\nYou have Python {sys.version.split()[0]}.")
    sys.exit(1)

gui.main()
