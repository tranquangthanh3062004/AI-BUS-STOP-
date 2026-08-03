import time
from typing import Dict, Any

class SessionManager:
    def __init__(self, ttl_seconds: int = 300):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def get_session(self, session_id: str) -> dict:
        self._cleanup()
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "intent": None,
                "origin": None,
                "destination": None,
                "last_active": time.time()
            }
        else:
            self.sessions[session_id]["last_active"] = time.time()
        return self.sessions[session_id]

    def update_session(self, session_id: str, intent: str = None, origin: str = None, destination: str = None):
        session = self.get_session(session_id)
        if intent:
            session["intent"] = intent
        if origin:
            session["origin"] = origin
        if destination:
            session["destination"] = destination

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def _cleanup(self):
        now = time.time()
        expired = [sid for sid, data in self.sessions.items() if now - data["last_active"] > self.ttl_seconds]
        for sid in expired:
            del self.sessions[sid]
