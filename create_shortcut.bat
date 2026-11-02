@echo off
rem ============================================================================
rem  create_shortcut.bat  [NEW]
rem  Double-click once: puts a "MIPS Simulator" icon on your Desktop.
rem  The icon opens sim\gui.py with pythonw (no console window).
rem  Needs Python 3.10+ installed. Run it again if you move this folder.
rem ============================================================================
setlocal
set "HERE=%~dp0"
set "PYW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW for /f "delims=" %%i in ('where pyw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW (
    echo Could not find Python. Install Python 3.10 or newer from python.org
    echo and tick "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\MIPS Simulator.lnk');" ^
  "$s.TargetPath = '%PYW%';" ^
  "$s.Arguments = '\"%HERE%sim\gui.py\"';" ^
  "$s.WorkingDirectory = '%HERE%sim';" ^
  "$s.IconLocation = '%HERE%sim\icon.ico';" ^
  "$s.Description = 'MIPS Simulator';" ^
  "$s.Save()"
if errorlevel 1 (
    echo Could not create the shortcut.
    pause
    exit /b 1
)
echo Done. Double-click "MIPS Simulator" on your Desktop to open the program.
pause
