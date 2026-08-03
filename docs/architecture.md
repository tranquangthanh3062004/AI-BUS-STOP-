# Sơ đồ Kiến trúc Hệ thống (Architecture Diagram)

Sơ đồ dưới đây mô tả kiến trúc tổng thể của AI Smart Bus Stop Assistant với luồng xử lý Online/Offline Hybrid.

```mermaid
graph TD
    %% User Interface
    subgraph UI[Kiosk Interface - Frontend]
        HTML[index.html / map.html]
        Voice[Web Speech API STT/TTS]
        Map[Leaflet Offline Map]
        Admin[Admin Dashboard]
    end

    %% Network Failover
    NetMon((Network Monitor))

    %% Backend Server
    subgraph BE[FastAPI Backend - Edge Node]
        API_Chat[/api/chat]
        API_Status[/api/status]
        
        subgraph Pipeline[AI Pipeline]
            Intent[Intent Classifier]
            Session[Session Manager]
            Val[Answer Validator / Guardrails]
            Sec[Security Sanitizer]
        end
        
        subgraph RAG[Retrieval-Augmented Generation]
            LocalRetriever[Local Retriever]
            Embedder[Gemini Embedder]
            FTS5[(SQLite FTS5 Keyword)]
            Chroma[(ChromaDB Vector)]
        end
        
        subgraph LLM[LLM Engine]
            Ollama[Ollama API - Qwen/Llama3]
            GGUF[llama.cpp - Fallback]
            Summ[Deterministic Summarizer]
        end
    end

    %% Database
    subgraph DB[Knowledge Base]
        SQLite[(local_transit.db)]
        DataFiles[Text / JSON Files]
    end

    %% Connections
    HTML <--> |JSON REST| API_Chat
    Admin <--> |JSON REST| API_Status
    NetMon -.-> |Toggle Mode| BE
    
    API_Chat --> Sec
    Sec --> Session
    Session --> Intent
    
    Intent --> |ROUTE_QUERY/FARE_QUERY| LocalRetriever
    LocalRetriever --> |Vector Search| Embedder
    Embedder --> Chroma
    LocalRetriever -.-> |Fallback Keyword| FTS5
    
    LocalRetriever --> LLM
    LLM --> Val
    Val --> Session
    Session --> API_Chat
    
    FTS5 <--> SQLite
    Chroma <--> DataFiles
```
