@echo off
setlocal enabledelayedexpansion
title AI Career Intelligence — One-Click Startup
chcp 65001 >nul
cd /d "%~dp0"

echo ╔══════════════════════════════════════════════════════════════╗
echo ║     AI Career Intelligence — One-Click Startup              ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Frontend: http://localhost:3000  (Next.js 14)              ║
echo ║  Backend : http://localhost:8000  (FastAPI)                 ║
echo ║  API Docs: http://localhost:8000/docs                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Kill existing processes on ports 3000 and 8000
echo [Cleanup] Checking ports 3000 and 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":3000 "') do (
    taskkill /pid %%a /f >nul 2>&1 && echo   Killed process on port 3000
)
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000 "') do (
    taskkill /pid %%a /f >nul 2>&1 && echo   Killed process on port 8000
)

:: Start Backend
echo.
echo [Backend] Starting FastAPI on http://localhost:8000 ...
start "Backend — FastAPI" cmd /c "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload ^& echo. ^& echo Backend stopped. ^& pause"

:: Wait a moment for backend to initialize
echo [Backend] Initializing (3s)...
ping -n 4 127.0.0.1 >nul

:: Start Frontend
echo.
echo [Frontend] Starting Next.js on http://localhost:3000 ...
start "Frontend — Next.js" cmd /c "cd frontend ^&^& npm run dev ^& echo. ^& echo Frontend stopped. ^& pause"

:: Wait for frontend to be ready
echo [Frontend] Initializing (5s)...
ping -n 6 127.0.0.1 >nul

:: Health check loop
echo.
echo [Health Check] Waiting for services...
set READY=0

for /L %%i in (1,1,30) do (
    :: Check backend
    curl -s -o nul -w "%%{http_code}" http://localhost:8000/health 2>nul | find "200" >nul
    if not errorlevel 1 (
        if "!READY!"=="0" (
            echo   ✓ Backend ready at http://localhost:8000
        )
    )

    :: Check frontend
    curl -s -o nul -w "%%{http_code}" http://localhost:3000 2>nul | find "200" >nul
    if not errorlevel 1 (
        if "!READY!"=="0" (
            echo   ✓ Frontend ready at http://localhost:3000
            set READY=1
        )
    )

    if "!READY!"=="1" (
        echo.
        echo ╔══════════════════════════════════════════════════════════════╗
        echo ║  🚀 All services are running!                                ║
        echo ║                                                              ║
        echo ║  Open your browser: http://localhost:3000                    ║
        echo ╚══════════════════════════════════════════════════════════════╝
        echo.
        start http://localhost:3000
        pause
        exit /b 0
    )

    ping -n 2 127.0.0.1 >nul
)

echo.
echo ⚠ Some services did not start in time.
echo    Backend:  http://localhost:8000/docs
echo    Frontend: http://localhost:3000
pause
