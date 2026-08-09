@echo off
chcp 65001 > nul
title AI Smart Bus Stop Launcher
echo ==============================================
echo  KHOI DONG HE THONG AI SMART BUS STOP v2.0
echo  (Local AI - Powered by Qwen via Ollama)
echo ==============================================
echo.

:: Luon cd ve thu muc chua file bat nay
cd /d "%~dp0"

:: Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python 3.10+ truoc.
    pause
    exit /b 1
)

:: Kill any existing process on port 8000
echo [0/3] Don dep process cu tren port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    if not "%%a"=="0" (
        taskkill /F /PID %%a > nul 2>&1
    )
)
timeout /t 2 /nobreak >nul

:: Kiem tra Ollama
echo [*] Kiem tra Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [CANH BAO] Ollama chua chay! He thong se dung Local Summarizer.
    echo [CANH BAO] De co AI tot hon, hay khoi dong Ollama truoc voi model qwen2.5:3b
    echo.
) else (
    echo [OK] Ollama dang chay!
)

echo.
echo [1/3] Khoi dong Backend Server (port 8000)...
start "Backend Server - AI Smart Bus Stop" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info"

echo.
echo DANG CHO BACKEND KHOI DONG (10 GIAY)...
timeout /t 10 /nobreak >nul

echo.
echo [2/3] Kiem tra ket noi...
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/status', timeout=5); print('[OK] Backend da san sang!')" 2>nul || echo [WARN] Backend co the chua san sang - vui long cho them...

echo.
echo [3/3] Mo Giao dien Kiosk UI...
start "" "http://localhost:8000"

echo.
echo ==============================================
echo  HOAN TAT!
echo  Backend : http://localhost:8000
echo  Kiosk UI: http://localhost:8000 (Auto-open)
echo  AI Model: Qwen 2.5 (Local Ollama)
echo ==============================================
echo.
echo (De tat he thong, dong cua so 'Backend Server')
echo.
pause
