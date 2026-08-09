"""
backend/main.py
FastAPI Server for AI Smart Bus Stop Assistant.
Supports both Online and Offline AI Assistant modes, with real-time Network Failover,
Input Security Sanitization, and Structured Logging.
"""

import os
import sys
import time
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.config import settings
from shared.security import sanitize_input_text
from shared.logger import logger
from shared.schemas import QueryRequest, OfflineResponse
from edge_ai.offline_pipeline import OfflineAIAssistant
from backend.online_pipeline import OnlineAIAssistant
from sync_service.network_monitor import NetworkMonitor

import threading
from collections import defaultdict

# Simple In-Memory Rate Limiter (Max 10 requests per minute per session)
rate_limits = defaultdict(lambda: {"count": 0, "reset_time": time.time() + 60})


# Global System Manager for Thread-Safety
class SystemManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SystemManager, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.offline_assistant = OfflineAIAssistant()
        self.online_assistant = OnlineAIAssistant(offline_assistant=self.offline_assistant)
        self.network_monitor = NetworkMonitor()
        self.network_mode = "OFFLINE"  # Default to LOCAL AI (Qwen via Ollama) — no cloud API needed
        self.manual_override = False
        self.station_id = settings.station_id
        self.station_name = settings.station_name
        self.last_ping_status = True
        self.state_lock = threading.Lock()

    def get_state_dict(self):
        # Return a dictionary ref to sync with NetworkMonitor
        return self.__dict__

    def update_network_mode(self, mode: str, manual: bool = False):
        with self.state_lock:
            self.network_mode = mode
            if manual:
                self.manual_override = True

system_manager = SystemManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version} on station '{settings.station_name}'...")
    logger.info("Local SQLite Transit Database, Vector Index & AI Pipelines loaded successfully.")
    # Start Network Monitor background loop
    network_mon = system_manager.network_monitor
    network_mon.start(state_dict=system_manager.get_state_dict())
    yield
    # Cleanup on shutdown
    network_mon.stop()
    logger.info(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="Backend API for Smart Bus Stop Kiosk with Offline Local AI Pipeline",
    version=settings.app_version,
    lifespan=lifespan
)

# Enable CORS for local testing and Kiosk UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., description="Nội dung câu hỏi của hành khách")
    session_id: Optional[str] = Field(default="default_session")
    force_offline: Optional[bool] = Field(default=False, description="Ép buộc dùng Offline Pipeline")
    force_online: Optional[bool] = Field(default=False, description="Ép buộc dùng Online Pipeline")


class NetworkToggleRequest(BaseModel):
    mode: str = Field(..., description="ONLINE hoặc OFFLINE")


@app.get("/api/status")
def get_system_status():
    """Lấy thông tin trạng thái hệ thống Kiosk."""
    offline_assistant = system_manager.offline_assistant
    llm_active = False
    active_model = "local_summarizer"
    if offline_assistant and hasattr(offline_assistant, "llm_engine"):
        llm_active = offline_assistant.llm_engine.ollama_active
        if llm_active:
            active_model = offline_assistant.llm_engine.active_ollama_model

    return {
        "status": "HEALTHY",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "network_mode": system_manager.network_mode,
        "manual_override": system_manager.manual_override,
        "station_id": system_manager.station_id,
        "station_name": system_manager.station_name,
        "llm_engine_status": "ACTIVE" if llm_active else "SUMMARIZER_FALLBACK",
        "active_model": active_model,
        "local_routes_indexed": 136,
        "local_stops_indexed": 590,
        "timestamp": time.time()
    }


@app.post("/api/toggle-network")
def toggle_network_mode(req: NetworkToggleRequest):
    """Chuyển đổi trạng thái mạng (ONLINE / OFFLINE) để test."""
    mode = req.mode.upper()
    if mode not in ["ONLINE", "OFFLINE"]:
        raise HTTPException(status_code=400, detail="Mode must be ONLINE or OFFLINE")
    system_manager.update_network_mode(mode, manual=True)
    logger.info(f"Manual network mode toggle: set to {mode} (Manual Override Active)")
    return {
        "message": f"System network mode updated to {mode}",
        "network_mode": mode,
        "manual_override": True
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """
    API Xử lý hội thoại chính của Kiosk.
    Đã qua lớp Input Security Sanitization & Failover.
    """
    session_id = req.session_id or "default_session"
    
    # Rate limiting check (10 requests per minute)
    now = time.time()
    if now > rate_limits[session_id]["reset_time"]:
        rate_limits[session_id] = {"count": 1, "reset_time": now + 60}
    else:
        if rate_limits[session_id]["count"] >= 10:
            logger.warning(f"Rate limit exceeded for session {session_id}")
            raise HTTPException(status_code=429, detail="Quá nhiều yêu cầu. Vui lòng thử lại sau 1 phút.")
        rate_limits[session_id]["count"] += 1

    raw_user_msg = req.message
    
    # 1. Input Security Sanitization
    sanitized_msg = sanitize_input_text(raw_user_msg)

    if not sanitized_msg:
        raise HTTPException(status_code=400, detail="Message is empty or contains invalid content")

    use_online = system_manager.network_mode == "ONLINE" or req.force_online
    use_offline = not use_online

    logger.info(f"Processing chat request: '{sanitized_msg}' | Mode: {'OFFLINE' if use_offline else 'ONLINE'}")

    query_req = QueryRequest(raw_text=sanitized_msg, session_id=req.session_id)

    if use_offline:
        offline_assistant = system_manager.offline_assistant
        res: OfflineResponse = offline_assistant.process_query(query_req)

        logger.info(f"Offline response generated in {res.execution_time_ms} ms | Status: {res.status}")
        return {
            "status": res.status,
            "reply": res.answer_text,
            "intent": res.intent,
            "processing_time_ms": res.execution_time_ms,
            "mode": "HỆ_THỐNG",
            "recommendations": [r.model_dump() for r in res.recommendations],
            "sources": res.sources_used
        }
    else:
        # Lấy Google Maps Data và chạy Gemini API
        online_assistant = system_manager.online_assistant
        res: OfflineResponse = online_assistant.process_query(query_req)

        logger.info(f"Online response generated in {res.execution_time_ms} ms | Status: {res.status}")
        return {
            "status": res.status,
            "reply": res.answer_text,
            "intent": res.intent,
            "processing_time_ms": res.execution_time_ms,
            "mode": "HỆ_THỐNG",
            "recommendations": [r.model_dump() for r in res.recommendations],
            "sources": res.sources_used
        }


# Mount static directories
UI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kiosk_ui"))
ADMIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin_ui"))

if os.path.exists(ADMIN_DIR):
    app.mount("/admin", StaticFiles(directory=ADMIN_DIR, html=True), name="admin_ui")
if os.path.exists(UI_DIR):
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=True)

