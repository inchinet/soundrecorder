@echo off
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
REM call "%~dp0venv\Scripts\activate"
call venv\Scripts\activate

REM echo Installed Python:
REM venv\Scripts\python.exe --version

REM echo Installing dependencies...
REM venv\Scripts\python.exe -m pip install --upgrade pip
REM venv\Scripts\python.exe -m pip install -r requirements.txt
REM  if %errorlevel% neq 0 (
REM     echo Error installing requirements!
REM     pause
REM     exit /b %errorlevel%
REM )

REM echo Listing installed packages:
REM  venv\Scripts\python.exe -m pip freeze

echo Starting Application...
venv\Scripts\python.exe src\main.py
if %errorlevel% neq 0 (
    echo Application crashed!
    pause
)


