@echo off
REM Batch script to update Claude configuration to use current development version

echo Updating Claude to use current development version of zen-mcp-server...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=%SCRIPT_DIR%.zen_venv\Scripts\python.exe
set SERVER_PATH=%SCRIPT_DIR%server.py

echo Current directory: %SCRIPT_DIR%
echo Python path: %PYTHON_PATH%
echo Server path: %SERVER_PATH%

REM Check if virtual environment Python exists
if not exist "%PYTHON_PATH%" (
    echo Error: Virtual environment Python not found at %PYTHON_PATH%
    echo Please run run-server.ps1 first to set up the environment
    exit /b 1
)

REM Check if server.py exists
if not exist "%SERVER_PATH%" (
    echo Error: server.py not found at %SERVER_PATH%
    exit /b 1
)

echo.
echo Updating configuration...

REM Try to update Claude CLI if available
where claude >nul 2>nul
if %errorlevel% == 0 (
    echo Updating Claude CLI configuration...
    claude mcp remove zen 2>nul
    claude mcp add -s user zen "%PYTHON_PATH%" "%SERVER_PATH%"
    if %errorlevel% == 0 (
        echo Claude CLI configuration updated successfully
    ) else (
        echo Warning: Could not update Claude CLI automatically
        echo Please manually update with:
        echo   claude mcp remove zen
        echo   claude mcp add -s user zen "%PYTHON_PATH%" "%SERVER_PATH%"
    )
) else (
    echo Claude CLI not found in PATH
)

echo.
echo Please restart Claude Code to apply changes.
echo Your Claude Code will now use the current development version.