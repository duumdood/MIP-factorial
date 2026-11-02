@echo off
rem ============================================================================
rem  build_exe.bat  [NEW]
rem  Double-click once: builds "MIPS Simulator.exe" in this folder with PyInstaller.
rem  The .exe runs on computers WITHOUT Python (e.g. the instructor's).
rem  Keep the .exe next to the programs and examples folders so the Examples menu works.
rem  Building takes about 1 minute and needs Python 3.10+ and an internet connection once.
rem ============================================================================
setlocal
cd /d "%~dp0"
set "HERE=%~dp0"
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "MIPS Simulator" ^
    --icon "%HERE%sim\icon.ico" ^
    --add-data "%HERE%sim\icon.png;." ^
    --paths "%HERE%sim" ^
    --distpath "%HERE%." --workpath "%HERE%build" --specpath "%HERE%build" ^
    "%HERE%sim\gui.py"
if errorlevel 1 goto fail
rmdir /s /q "%HERE%build"
echo.
echo Done: "MIPS Simulator.exe" is in this folder. Double-click it to open the program.
pause
exit /b 0
:fail
echo.
echo Build failed. Check the messages above.
pause
exit /b 1
