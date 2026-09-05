@echo off
REM exa_search.bat - web search helper (Exa API) for this project's agents.
REM Usage: exa_search.bat search "Latest news on Nvidia" --num 5 [--json]
REM        exa_search.bat contents https://exa.ai --max-chars 4000 [--json]
REM        exa_search.bat answer "What makes some LLMs better than others?" [--json]
REM Key: EXA_API_KEY in the project-root .env. Full help: exa_search.py --help
REM No pause on purpose - automation/agents must never hang on a keypress.

cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

if not exist ".venv\Scripts\python.exe" (
    echo [error] .venv not found. Rebuild it first - see HANDOFF.md section 4.
    exit /b 1
)

".venv\Scripts\python.exe" "%~dp0exa_search.py" %*
