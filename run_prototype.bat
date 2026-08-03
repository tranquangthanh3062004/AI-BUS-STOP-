@echo off
echo ==============================================
echo KHOI DONG PROTOTYPE KIOSK AI
echo ==============================================
echo.

echo [1/3] Cai dat thu vien Backend...
pip install -r requirements.txt

echo.
echo [2/3] Khoi dong Edge AI Backend (FastAPI)...
start "Edge AI Backend" cmd /c "cd edge_ai && python main.py"

echo.
echo DANG CHO BACKEND KHOI DONG (3 GIAY)...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] Mo Giao dien Kiosk UI (Trinh duyet)...
start "" "%cd%\kiosk_ui\index.html"

echo.
echo HOAN TAT! Ban co the the tuong tac tren trinh duyet!
pause
