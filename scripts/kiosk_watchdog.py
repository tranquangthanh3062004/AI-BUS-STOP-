"""
scripts/kiosk_watchdog.py
Production Edge Device Supervisor & Health Watchdog Daemon.
Monitors the Kiosk FastAPI Backend process, auto-restarts on failure,
cleans up memory leaks, and rotates application logs to prevent eMMC/SSD overflow.
"""

import os
import sys
import time
import urllib.request
import json
import subprocess
import shutil

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HEALTH_URL = "http://127.0.0.1:8000/api/health"
METRICS_URL = "http://127.0.0.1:8000/api/metrics"
LOG_DIR = os.path.join(ROOT_DIR, "logs")
MAIN_LOG = os.path.join(LOG_DIR, "kiosk_app.log")
MAX_LOG_SIZE_MB = 20
MAX_FAILURES = 3
CHECK_INTERVAL_SEC = 15

def log_watchdog(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [WATCHDOG] {msg}"
    print(formatted)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "watchdog.log"), "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def check_kiosk_health() -> bool:
    try:
        req = urllib.request.Request(HEALTH_URL)
        with urllib.request.urlopen(req, timeout=4) as res:
            if res.status == 200:
                data = json.loads(res.read().decode('utf-8'))
                return data.get("status") in ["UP", "HEALTHY", "DEGRADED"]
    except Exception as e:
        log_watchdog(f"Health check failed: {e}")
    return False

def rotate_logs_if_needed():
    try:
        if os.path.exists(MAIN_LOG):
            size_mb = os.path.getsize(MAIN_LOG) / (1024 * 1024)
            if size_mb > MAX_LOG_SIZE_MB:
                backup_name = os.path.join(LOG_DIR, f"kiosk_app_{time.strftime('%Y%m%d_%H%M%S')}.log")
                shutil.move(MAIN_LOG, backup_name)
                log_watchdog(f"Rotated log file ({size_mb:.1f}MB) -> {os.path.basename(backup_name)}")
                # Retain only last 5 rotated logs
                all_logs = sorted([f for f in os.listdir(LOG_DIR) if f.startswith("kiosk_app_") and f.endswith(".log")])
                while len(all_logs) > 5:
                    old_file = os.path.join(LOG_DIR, all_logs.pop(0))
                    os.remove(old_file)
                    log_watchdog(f"Removed old rotated log: {old_file}")
    except Exception as e:
        log_watchdog(f"Log rotation error: {e}")

def restart_backend_process():
    log_watchdog("Restarting Kiosk Backend Process...")
    # On Windows: Taskkill any existing process on port 8000
    if sys.platform == "win32":
        try:
            # Kill processes listening on 8000
            subprocess.run("for /f \"tokens=5\" %a in ('netstat -aon ^| find \":8000\"') do taskkill /f /pid %a", shell=True, capture_output=True)
        except Exception:
            pass
    # Launch new backend process
    cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    subprocess.Popen(cmd, cwd=ROOT_DIR)
    log_watchdog("Spawned new backend process on port 8000.")

def run_supervisor_loop():
    log_watchdog("Starting Production Kiosk Supervisor Daemon...")
    consecutive_failures = 0

    while True:
        rotate_logs_if_needed()
        is_healthy = check_kiosk_health()

        if is_healthy:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            log_watchdog(f"Warning: Health check failed ({consecutive_failures}/{MAX_FAILURES})")
            if consecutive_failures >= MAX_FAILURES:
                log_watchdog("CRITICAL: Maximum failure threshold reached! Initiating auto-recovery...")
                restart_backend_process()
                consecutive_failures = 0
                time.sleep(10) # Grace period for startup

        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    run_supervisor_loop()
