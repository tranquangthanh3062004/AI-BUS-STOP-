"""
shared/config.py
Centralized Configuration Settings using Pydantic.
Manages environment variables, default values, database paths, and hardware parameters.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Smart Bus Stop Assistant"
    app_version: str = "2.0.0-production"
    environment: str = "production"
    
    # Server Host & Port
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Station Parameters
    station_id: str = "STATION_001_MY_DINH"
    station_name: str = "Trạm Xe Buýt Bến Xe Mỹ Đình - Hà Nội"
    default_fare_vnd: int = 7000
    
    # File Paths
    base_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path: str = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "local_transit.db")
    faq_path: str = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "faq_store.json")
    vector_db_path: str = os.path.join(os.path.dirname(__file__), "..", "vector_db", "local_index.json")
    chroma_db_path: str = os.path.join(os.path.dirname(__file__), "..", "vector_db", "chroma_db")
    prompts_dir: str = os.path.join(os.path.dirname(__file__), "..", "prompts")
    log_file_path: str = os.path.join(os.path.dirname(__file__), "..", "logs", "kiosk_app.log")
    
    # Cloud & External API Settings (Online Pipeline)
    google_maps_api_key: Optional[str] = None
    cloud_llm_api_key: Optional[str] = None
    cloud_llm_provider: str = "simulated"  # "google", "openai", or "simulated"
    
    # RAG Settings
    vector_rag_enabled: bool = False
    gemini_api_key: Optional[str] = None
    
    # Failover & Network Check
    ping_target_host: str = "8.8.8.8"
    ping_interval_sec: int = 10
    ping_timeout_sec: float = 2.0


settings = AppSettings()

