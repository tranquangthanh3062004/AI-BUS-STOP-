@echo off
chcp 65001 > nul
title AI Smart Bus Stop - Production Launcher
echo ==============================================================
echo   TRẠM XE BUÝT THÔNG MINH - PRODUCTION KIOSK LAUNCHER
echo   Bảo vệ 24/7 với Kiosk Watchdog Daemon & Auto-Recovery
echo ==============================================================
echo.

cd /d "%~dp0"

:: Đảm bảo thư mục logs tồn tại
if not exist "logs" mkdir logs

:: 1. Dọn dẹp tiến trình cũ trên port 8000
echo [1/4] Dọn dẹp các tiến trình cũ trên port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    if not "%%a"=="0" (
        taskkill /F /PID %%a > nul 2>&1
    )
)
timeout /t 1 /nobreak >nul

:: 2. Khởi động Backend Server
echo [2/4] Khởi động AI Edge Server (Uvicorn)...
start "AI Bus Stop Backend" /min cmd /c "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info >> logs\backend_stdout.log 2>&1"

:: 3. Chờ Backend sẵn sàng
echo [3/4] Đang kiểm tra trạng thái sức khỏe máy chủ...
timeout /t 3 /nobreak >nul
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=6); print('      -> [OK] Trạm AI Edge đã sẵn sàng!')"

:: 4. Khởi động Watchdog Supervisor
echo [4/4] Khởi động Kiosk Watchdog & Auto-Recovery Daemon...
start "Kiosk Watchdog Supervisor" /min cmd /c "cd /d "%~dp0" && python scripts\kiosk_watchdog.py"

echo.
echo ==============================================================
echo   HỆ THỐNG ĐÃ SẴN SÀNG TRIỂN KHAI PRODUCTION!
echo   Kiosk Endpoint : http://localhost:8000
echo   Health Check   : http://localhost:8000/api/health
echo   Telemetry Metrics: http://localhost:8000/api/metrics
echo ==============================================================
echo.

:: Mở giao diện Kiosk (Chrome / Edge hoặc trình duyệt mặc định)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --kiosk http://localhost:8000 --edge-kiosk-type=fullscreen --no-first-run
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:8000 --no-first-run
) else (
    start "" "http://localhost:8000"
)

exit /b 0
