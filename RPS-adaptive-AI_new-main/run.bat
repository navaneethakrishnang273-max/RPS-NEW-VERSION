@echo off
echo ===================================================
echo   Rock-Paper-Scissors Opponent Modeling Launcher
echo ===================================================
set PYTHON_CMD=python
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
)

echo.
echo [1] Running simulation benchmarks...
"%PYTHON_CMD%" src\rps_agent.py
echo.
echo [2] Opening plot and starting interactive web app...
start "" "docs\winrate_plot.png"
start "" "http://localhost:5000"
"%PYTHON_CMD%" src\server.py
pause

