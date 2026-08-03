# Kiến trúc & Cấu trúc thư mục tối ưu (AI Smart Bus Stop)

Dự án này đã được tối ưu hóa, loại bỏ hoàn toàn các thư mục rác/cũ và tái tổ chức lại để chuẩn bị triển khai lên GitHub hoặc môi trường Production một cách chuyên nghiệp nhất.

## 📂 Sơ đồ cấu trúc (File Tree)

```text
AI BUS STOP/
├── backend/              # Core API Server & Online Scraper
│   ├── main.py           # FastAPI entrypoint, router & dependencies
│   ├── online_pipeline.py # Luồng xử lý Online (Web Scraper + LLM)
│   └── scraper_agent.py  # Playwright Crawler trích xuất data từ Google Maps
│
├── edge_ai/              # Offline AI & RAG Pipeline (Xử lý không cần Internet)
│   ├── intent_classifier.py # Phân loại ý định người dùng (Tư vấn, Báo lỗi, Tìm đường...)
│   ├── offline_pipeline.py  # Luồng xử lý Offline (Local Vector DB + LLM)
│   ├── session_manager.py   # Quản lý bộ nhớ phiên hội thoại người dùng
│   ├── session_resolver.py  # Xử lý context và ngữ cảnh ẩn
│   ├── transit_graph.py     # Đồ thị thuật toán tìm đường cục bộ
│   └── validator.py         # Kiểm duyệt Ảo Giác (Anti-Hallucination) bằng Regex và SQLite
│
├── local_llm/            # Module giao tiếp với Local LLM (Ollama)
│   └── llm_engine.py     
│
├── rag/                  # Retrieval-Augmented Generation
│   ├── chroma_store.py   # Tương tác với ChromaDB (Vector DB)
│   ├── gemini_embedder.py# Tạo Embedding model
│   └── local_retriever.py# Tìm kiếm Full-Text (FTS5) và Vector (Hybrid Search)
│
├── shared/               # Code dùng chung (Shared resources)
│   ├── config.py         # Cấu hình biến môi trường
│   ├── logger.py         # Cấu hình log hệ thống
│   ├── schemas.py        # Pydantic models (Data validation)
│   └── security.py       # Cấu hình bảo mật, API key
│
├── sync_service/         # Dịch vụ kiểm tra và đồng bộ trạng thái mạng
│   └── network_monitor.py
│
├── kiosk_ui/             # Giao diện người dùng tại trạm chờ (HTML/JS/CSS)
│   ├── index.html        # Giao diện chính (Chatbot & Bản đồ)
│   ├── map.html          # Layer bản đồ mở rộng
│   └── static/           # CSS, Fonts, Images, JS (Leaflet, Routing Machine)
│
├── data/                 # Raw data (TXT, JSON) dùng để xây dựng Knowledge Base
│   ├── hanoi/            # Chứa các file text tài liệu về xe buýt Hà Nội
│   ├── finetune_gtcc.jsonl 
│   └── transit.db        
│
├── knowledge_base/       # Cơ sở dữ liệu đã biên dịch (Compiled Data)
│   └── local_transit.db  # SQLite Database chứa lộ trình, bến bãi, FTS5 table
│
├── vector_db/            # Thư mục lưu trữ index của ChromaDB
│   └── chroma_db/
│
├── scripts/              # Các script hỗ trợ (Automation)
│   ├── build_knowledge_base.py # Chạy để tạo SQLite từ file txt
│   ├── build_vector_index.py   # Chạy để tạo ChromaDB từ file txt
│   ├── download_fonts.py
│   └── download_libs.py
│
├── tests/                # Unit test & End-to-End Test (Pytest)
│   ├── benchmark/        # Đánh giá hiệu suất LLM/RAG
│   ├── evaluate_rag.py   
│   ├── test_agentic.py
│   └── test_regex.py
│
├── docs/                 # Toàn bộ tài liệu, báo cáo đồ án, thiết kế kiến trúc
│   ├── architecture/     # Thiết kế hệ thống, sơ đồ khối
│   ├── thesis/           # File báo cáo đồ án gốc (.docx, .pdf)
│   ├── diagrams/         # Ảnh bản đồ, sơ đồ
│   ├── TECHNICAL_AUDIT_REPORT.md
│   ├── PRODUCTION_READY_REPORT.md
│   └── ... (Các file báo cáo Markdown khác)
│
├── start.bat             # Script chạy hệ thống tự động trên Windows (Click để chạy)
├── run_prototype.bat     
├── README.md             # Hướng dẫn chạy dự án 
├── pyproject.toml        
├── Dockerfile            # Cấu hình đóng gói Docker
├── docker-compose.yml    
└── requirements.txt      # Danh sách thư viện Python
```

## 🧹 Các điểm tối ưu đã thực hiện so với dự án cũ:
1. **Dọn dẹp rác:** Đã loại bỏ hoàn toàn các folder trống không có tác dụng (`frontend/`, `dashboard/`, `admin_ui/`, `deployment/`, v.v.).
2. **Loại bỏ Cache:** Loại bỏ các folder `.pytest_cache`, `.deepeval`, `__pycache__`, `logs` rác.
3. **Quy hoạch Tài liệu:** Toàn bộ các file `.md` và `.docx` nháp, báo cáo vứt ngoài Root đã được đưa gọn gàng vào trong thư mục `docs/`.
4. **Chuẩn hóa Root:** Root thư mục hiện tại chỉ chứa mã nguồn chạy trực tiếp (`backend`, `edge_ai`, `kiosk_ui`,...), các file cấu hình chuẩn (`Dockerfile`, `.env`) và script khởi động. 

Cấu trúc này đảm bảo 100% tiêu chuẩn của một dự án Open Source chuyên nghiệp trên GitHub.
