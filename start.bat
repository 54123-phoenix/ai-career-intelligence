@echo off
title AI Career Intelligence System
cd /d "%~dp0"

echo === AI Career Intelligence System ===
echo.

:: Kill anything on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000 "') do taskkill /pid %%a /f >nul 2>&1

:: Try Docker first
where docker >nul 2>&1
if %errorlevel% equ 0 (
    echo [Docker] Starting...
    docker-compose up --build -d
    goto :wait
)

echo [Direct mode] Starting backend on http://localhost:8000
echo.

:: Start uvicorn in a new window
start "Backend" cmd /c "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 & pause"

:wait
echo Waiting for backend...
ping -n 4 127.0.0.1 >nul

for /L %%i in (1,1,20) do (
    curl -s -o nul -w "%%{http_code}" http://localhost:8000/health 2>nul | find "200" >nul
    if not errorlevel 1 (
        echo Ready.
        start http://localhost:8000/docs
        echo   API Docs : http://localhost:8000/docs
        pause
        exit
    )
    ping -n 3 127.0.0.1 >nul
)

echo Timed out. Check the Backend window for errors.
pause
