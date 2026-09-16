@echo off
REM diacritize.bat - interactive Arabic diacritization chat with the D-line GOLD
REM model (stage2b2500, 30M, best-gate snapshot at step 2500).
REM Double-click or run from any terminal. Optional args pass through, e.g.:
REM   diacritize.bat --file my_text.txt
REM   diacritize.bat --text "<arabic sentence>"
REM Inside the REPL: type/paste Arabic, press Enter -> diacritized output.
REM Type q (or Ctrl+Z then Enter) to quit.

chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [error] .venv not found - rebuild it first, see ENVIRONMENT.md.
    pause
    exit /b 1
)
if not exist "runs\diac\stage2b2500\final\model.pt" (
    echo [error] GOLD model not found: runs\diac\stage2b2500\final\model.pt
    echo         (it was never trained/moved - see HANDOFF.md / research/FINAL_REPORT.md)
    pause
    exit /b 1
)

REM Single-GPU guard: warn (not block) if a training job is chewing the GPU.
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I "python" >nul && echo [warn] A python process is running - if it is a TRAINING job, wait for it to finish first (single-GPU rule).

".venv\Scripts\python.exe" -X utf8 diacritizer\scripts\diacritize.py %*
echo.
echo [diacritize.bat session ended - exit code %errorlevel%]
pause
