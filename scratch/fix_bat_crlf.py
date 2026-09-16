import pathlib

BS = chr(92)
gold = BS.join(["runs", "diac", "stage2b2500", "final", "model.pt"])
bat = "@echo off\n".replace("\n", chr(13) + chr(10))
lines = [
    "@echo off",
    "REM diacritize.bat - interactive Arabic diacritization chat with the D-line GOLD",
    "REM model (stage2b2500, 30M, best-gate snapshot at step 2500).",
    "REM Double-click, or run from any terminal. Extra args pass through:",
    'REM   diacritize.bat --file my_text.txt',
    'REM   diacritize.bat --text "<arabic sentence>"',
    "REM In interactive mode: type/paste Arabic -> diacritized output; q quits.",
    "",
    "chcp 65001 >nul",
    "set PYTHONIOENCODING=utf-8",
    'cd /d "%~dp0"',
    "",
    'if not exist ".venv' + BS + 'Scripts' + BS + 'python.exe" (',
    "    echo [error] .venv not found - rebuild it first, see ENVIRONMENT.md.",
    "    pause",
    "    exit /b 1",
    ")",
    'if not exist "' + gold + '" (',
    "    echo [error] GOLD model missing: " + gold,
    "    echo         see HANDOFF.md / research/FINAL_REPORT.md",
    "    pause",
    "    exit /b 1",
    ")",
    "",
    "echo [diacritize] loading the GOLD model... first answer needs a few seconds.",
    '".venv' + BS + 'Scripts' + BS + 'python.exe" -X utf8 diacritizer' + BS + 'scripts' + BS + 'diacritize.py %*',
    "echo.",
    "echo [diacritize] session ended",
    "pause",
]
text = chr(13) + chr(10) if False else "".join([l + chr(13) + chr(10) for l in lines])
p = pathlib.Path("diacritize.bat")
p.write_bytes(text.encode("utf-8"))
print("bat rebuilt, bytes:", p.stat().st_size)
