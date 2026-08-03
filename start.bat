@echo off
chcp 65001 > nul
title AI Smart Bus Stop Launcher
echo ==============================================
echo  KHOI DONG HE THONG AI SMART BUS STOP v2.0
echo ==============================================
echo.

:: Kill any existing process on port 8000
echo [0/3] Don dep process cu tren port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " 2^>nul') do (
    if not "%%a"=="0" (
        taskkill /F /PID %%a > nul 2>&1
    )
)
timeout /t 1 /nobreak >nul

echo [1/3] Khoi dong Backend Server (port 8000)...
start "Backend Server - AI Smart Bus Stop" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info"

echo.
echo DANG CHO BACKEND KHOI DONG (8 GIAY)...
timeout /t 8 /nobreak >nul

echo.
echo [2/3] Kiem tra ket noi...
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/status', timeout=5); print('[OK] Backend da san sang!')" 2>nul || echo [WARN] Backend co the chua san sang - vui long cho them...

echo.
echo [3/3] Mo Giao dien Kiosk UI...
start "" "http://localhost:8000"

echo.
echo HOAN TAT!
echo Backend: http://localhost:8000
echo Kiosk UI: http://localhost:8000 (Auto-open)
echo.
echo (De tat he thong, dong cua so 'Backend Server')
echo.
pause
