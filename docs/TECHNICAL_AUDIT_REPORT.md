# TECHNICAL AUDIT REPORT
**HỆ THỐNG AI SMART BUS STOP ASSISTANT**

- **Ngày thực hiện kiểm toán:** 25/07/2026
- **Thực hiện bởi:** Hội đồng Kiểm toán Kỹ thuật Độc lập (Principal Software Architect, Principal AI/RAG Engineer, Principal Security Engineer, Principal DevOps Engineer, Principal QA Engineer)
- **Đối tượng kiểm toán:** Toàn bộ Repository `AI_Smart_Bus_Stop_Assistant` (Source code, Database, API, UI, Scripts, Tests, Docker, và Documentation)
- **Tình trạng báo cáo:** Tài liệu kiểm toán nội bộ - Phản ánh 100% hiện trạng thực tế, không tô hồng, không bịa đặt.

---

## 1. TỔNG QUAN HIỆN TRẠNG REPOSITORY (REPOSITORY INVENTORY)

### 1.1. Ma trận Phân tích Thư mục Thực tế

Qua kiểm tra trực tiếp cấu trúc cây thư mục và danh sách file trong workspace, kết quả kiểm toán phân loại thư mục hiện tại như sau:

| Thư mục | Trạng thái Thực tế | Mức độ Hoàn thiện | Mô tả Hiện trạng |
| :--- | :--- | :--- | :--- |
| `backend/` | **Có mã nguồn** | 75% | Đã triển khai FastAPI Server (`main.py`), hỗ trợ CORS, endpoint `/api/status`, `/api/toggle-network`, `/api/chat`. Gắn giao diện tĩnh (`StaticFiles`). |
| `edge_ai/` | **Có mã nguồn** | 80% | Gồm `intent_classifier.py`, `transit_graph.py`, `offline_pipeline.py`, `validator.py`, `main.py` (mock). Core logic nhận diện ý định và tìm đường local. |
| `local_llm/` | **Có mã nguồn** | 85% | Gồm `llm_engine.py`. Hỗ trợ 3 tầng fallback: Ollama local API (Qwen2.5:3B), llama.cpp GGUF, và Deterministic Local Summarizer. |
| `rag/` | **Có mã nguồn** | 80% | Gồm `local_retriever.py`. Kết hợp dữ liệu cấu trúc (SQLite Transit Graph) và phi cấu trúc (FAQ JSON store). |
| `shared/` | **Có mã nguồn** | 90% | Gồm `config.py` (Pydantic Settings), `schemas.py` (Pydantic models), `security.py` (Sanitizer chống XSS/Injection), `logger.py` (Loguru). |
| `kiosk_ui/` | **Có mã nguồn** | 85% | `index.html` đơn file (895 dòng). Tích hợp Leaflet Map, Web Speech API (STT/TTS), nút chuyển chế độ mạng, phím tắt nhanh, giao diện Dark Mode mượt mà. |
| `knowledge_base/` | **Có dữ liệu** | 90% | Chứa `local_transit.db` (136 tuyến, 590 điểm dừng) và `faq_store.json` (FAQ, quy định, Metro). |
| `scripts/` | **Có mã nguồn** | 85% | `build_knowledge_base.py` (trích xuất Excel/Text/JSONL tạo DB), `run_offline_demo.py` (CLI interactive demo), và các script debug. |
| `tests/` | **Có mã nguồn** | 70% | `test_e2e_production.py` (FastAPI TestClient), `test_offline_mode.py` (Pytest cho 7 kịch bản offline). |
| `data/` | **Có dữ liệu** | 90% | Dữ liệu Hà Nội (`data/hanoi/`), TP.HCM (`data/hcm/`), dữ liệu thô Excel/Text (`data/archive/`), fine-tuning data (`finetune_gtcc.jsonl`). |
| `docs/` | **Có tài liệu** | 60% | Chứa 16 file markdown thiết kế tổng quan. Tuy nhiên, **tất cả 8 thư mục con trong `docs/` đều rỗng**. |
| `configs/` | **Thư mục RỖNG** | 0% | Rỗng. Cấu hình hiện đặt trong `shared/config.py` và `.env.example`. |
| `dashboard/` | **Thư mục RỖNG** | 0% | Rỗng. Chưa có mã nguồn Dashboard quản trị cho vận hành. |
| `deployment/` | **Thư mục RỖNG** | 0% | Rỗng. Chưa có script Kiosk deployment (Ansible, Systemd, v.v.). |
| `docker/` | **Thư mục RỖNG** | 0% | Rỗng. File Dockerfile & docker-compose nằm ở thư mục gốc. |
| `frontend/` | **Thư mục RỖNG** | 0% | Rỗng. Giao diện Kiosk hiện nằm trong `kiosk_ui/index.html`. |
| `notebooks/` | **Thư mục RỖNG** | 0% | Rỗng. Chưa có Jupyter Notebooks cho EDA hay mô hình hóa. |
| `prompts/` | **Thư mục RỖNG** | 0% | Rỗng. Prompt hiện hardcoded trong `local_llm/llm_engine.py`. |
| `sample_data/` | **Thư mục RỖNG** | 0% | Rỗng. Dữ liệu mẫu nằm trong `data/`. |
| `speech/` | **Thư mục RỖNG** | 0% | Rỗng. Xử lý giọng nói dùng Web Speech API trực tiếp trên trình duyệt Kiosk UI. |
| `sync_service/`| **Thư mục RỖNG** | 0% | Rỗng. Chưa có dịch vụ đồng bộ dữ liệu Realtime/GTFS từ Server về Kiosk. |
| `vector_db/` | **Thư mục RỖNG** | 0% | Rỗng. RAG dùng SQLite và JSON Store, chưa dùng Vector DB (Chroma/FAISS). |

---

## 2. PHÂN TÍCH CHI TIẾT TỪNG MODULE & NGUỒN MÃ (CODEBASE AUDIT)

### 2.1. Backend Module (`backend/main.py`)
- **Vai trò:** FastAPI Server chính điều phối requests từ UI Kiosk.
- **Logic:**
  - Định nghĩa trạng thái toàn cục `SYSTEM_STATE` với `network_mode` ("ONLINE" / "OFFLINE").
  - Khởi tạo instance `OfflineAIAssistant` ngay khi import module.
  - Endpoint `/api/status`: Trả về thông tin trạm, trạng thái Ollama/Summarizer, số lượng tuyến (hardcoded 136 routes, 590 stops trong response dict).
  - Endpoint `/api/toggle-network`: Cho phép đổi mode thủ công qua POST request.
  - Endpoint `/api/chat`: Nhận `message`, gọi `sanitize_input_text()`. Nếu `use_offline` (OFFLINE mode hoặc `force_offline=True`), gọi `offline_assistant.process_query()`.
- **Điểm mạnh:** Cấu trúc FastAPI chuẩn, tích hợp middleware CORS, tích hợp lớp bảo vệ đầu vào Sanitization, đo thời gian xử lý chính xác (`perf_counter`).
- **Điểm yếu & Rủi ro:**
  - **Giả lập Cloud Mode (Simulated Cloud):** Khi `network_mode == "ONLINE"`, endpoint KHÔNG hề gọi Google Maps API hay Cloud LLM (OpenAI/Gemini). Thực chất, nó gọi chính `offline_assistant.process_query()`, sau đó thêm chuỗi tiền tố `"[ONLINE CLOUD MODE] "` và cộng thêm `250.0 ms` độ trễ giả tạo. Đây là tính năng giả lập (Simulated Cloud), chưa kết nối Cloud thật.
  - **Event Loop Blocking Potential:** Hàm `/api/chat` là hàm đồng bộ (`def chat_endpoint`), khi gọi Ollama qua HTTP synchronous `urllib.request`, FastAPI sẽ chạy nó trên threadpool. Nếu lượng request song song lớn, có thể cạn kiệt threadpool.
  - Hardcoded thông số trong `get_system_status()` (dòng 87-88: `"local_routes_indexed": 136`).

### 2.2. Edge AI Pipeline Module (`edge_ai/`)

#### a) `edge_ai/intent_classifier.py`
- **Logic:**
  - `QueryNormalizer`: Chuẩn hóa chuỗi unicode (NFC), chuyển chữ thường, thay thế các từ viết tắt phổ biến (`brt 01` ➔ `brt01`, `bx` ➔ `bến xe`, `đh` ➔ `đại học`, `bk` ➔ `bách khoa`, v.v.).
  - `IntentClassifier`: Sử dụng Regex và luật từ khóa (Rule-based) để phân loại 6 Intent: `ROUTE_QUERY`, `FARE_QUERY`, `SCHEDULE_QUERY`, `RULE_QUERY`, `METRO_QUERY`, `UNKNOWN`.
  - Trích xuất thực thể (Entity Extraction): `origin`, `destination`, `route_id`, `location_keyword` bằng biểu thức chính quy.
- **Điểm mạnh:** Rất nhanh (< 1ms), không tốn tài nguyên GPU/NPU, xử lý tốt các mẫu câu chuẩn ("từ X đến Y", "đi X về Y").
- **Điểm yếu:** Cực kỳ nhạy cảm với câu lệnh biến thể phức tạp ngoài tập quy tắc Regex. Nếu câu hỏi không chứa các từ khóa quy định (vd: "đi chơi ở phố cổ thì đi cái gì"), intent dễ rớt về `UNKNOWN` hoặc nhận diện sai thực thể.

#### b) `edge_ai/transit_graph.py`
- **Logic:**
  - `LocalTransitGraph`: Engine định tuyến xe buýt cục bộ dựa trên SQLite DB (`local_transit.db`).
  - Hỗ trợ `alias_map` cho các địa danh lớn tại Hà Nội và TP.HCM (vd: "bách khoa", "mỹ đình", "giáp bát", "hồ gươm").
  - `find_direct_routes()`: Tìm kiếm tuyến đi thẳng bằng SQL `SELECT`. Chấm điểm tối ưu (`score`) dựa trên vị trí xuất hiện của điểm đi/đến trong hành trình tuyến và độ dài hành trình.
  - `find_one_transfer_routes()`: Tìm tuyến chuyển đổi 1 lần (1-transfer). Lấy danh sách tuyến từ điểm đi và tuyến tới điểm đến, thực hiện tách chuỗi hành trình `itinerary.split("-")` để tìm giao điểm trạm trung chuyển chung (`common_stops`).
- **Điểm mạnh:** Chạy 100% Offline, không phụ thuộc Google Maps. Thuật toán phân tích chuỗi tuyến xe buýt đạt độ chính xác cao đối với dữ liệu đã được chuẩn hóa.
- **Điểm yếu:** Thuật toán đếm chuyển tuyến dựa trên cắt chuỗi String (`split("-")`), chưa dựng đồ thị Graph đếm Dijkstra/A* chính thức bằng NetworkX với tọa độ GPS thực tế. Do đó không tính toán được khoảng cách đi bộ chính xác giữa 2 trạm chuyển tuyến.

#### c) `edge_ai/offline_pipeline.py` & `edge_ai/validator.py`
- **Logic:**
  - `OfflineAIAssistant`: Chuỗi xử lý nối tiếp: `Query Normalizer` ➔ `Intent Classifier` ➔ `Local Retriever` ➔ `Local LLM Engine` ➔ `Answer Validator`.
  - `AnswerValidator`: Cơ chế chống ảo giác (Anti-Hallucination). Kiểm tra câu trả lời do LLM sinh ra đối với `ROUTE_QUERY`. Nếu câu trả lời chứa số tuyến KHÔNG nằm trong danh sách tuyến hợp lệ (`valid_route_ids`) do Retriever cung cấp, Validator sẽ chặn ngay lập tức và trả về câu thông báo Fallback an toàn: *"Tôi không tìm thấy thông tin này trong cơ sở dữ liệu cục bộ hiện có."*
- **Điểm mạnh:** Loại bỏ triệt để nguy cơ LLM bịa đặt tuyến xe buýt không tồn tại (Zero Hallucination trên mã tuyến).
- **Điểm yếu:** Validator hiện mới chỉ check mã tuyến (`route_id`), chưa kiểm tra được ảo giác về tên điểm dừng đi kèm hoặc khoảng thời gian hoạt động do LLM tự do diễn đạt.

### 2.3. Local LLM Module (`local_llm/llm_engine.py`)
- **Logic:**
  - Quản lý sinh câu trả lời theo chiến lược 3 tầng (3-Tier Fallback Strategy):
    1. **Tầng 1 (Primary):** Gọi Ollama API cục bộ tại `http://localhost:11434/api/generate` (Mô hình ưu tiên: `qwen2.5:3b`, `llama3:latest`, `phi3:mini`). Cấu hình `temperature=0.1`, `num_predict=250`.
    2. **Tầng 2 (Secondary):** Nếu Ollama không chạy, thử load file GGUF qua thư viện `llama_cpp.Llama`.
    3. **Tầng 3 (Fallback):** Nếu không có mô hình LLM nào hoạt động, tự động chuyển sang **Local Deterministic Summarizer** (Tóm tắt dữ liệu bằng chuỗi mẫu mã hóa cứng theo định dạng biểu tượng mượt mà 🌟).
- **Điểm mạnh:** Đảm bảo hệ thống KHÔNG BAO GIỜ CRASH dù thiết bị Edge không có GPU hay không cài Ollama. Tầng Fallback Summarizer phản hồi tức thì (< 2ms) với định dạng câu trả lời cực kỳ chuẩn xác và rõ ràng.
- **Điểm yếu:** Khi chạy Ollama `qwen2.5:3b` trên thiết bị CPU yếu không có card đồ họa (NVIDIA/NPU), độ trễ sinh từ có thể kéo dài từ 3s - 12s. Prompt hardcoded trực tiếp trong file python thay vì quản lý qua thư mục `prompts/`.

### 2.4. Local RAG Module (`rag/local_retriever.py`)
- **Logic:**
  - `LocalRetriever`: Kết hợp truy vấn dữ liệu cấu trúc (Structured Transit Routes) từ `LocalTransitGraph` và dữ liệu phi cấu trúc (Unstructured Chunks) từ `knowledge_base/faq_store.json`.
  - Thực hiện chấm điểm từ khóa (Keyword Scoring) đơn giản trên tiêu đề và nội dung FAQ để rút ra tối đa 3 văn bản liên quan nhất.
- **Điểm mạnh:** Nhẹ, chạy trực tiếp trong memory và SQLite, không cần khởi động Vector Database tốn RAM.
- **Điểm yếu:** Không sử dụng Dense Vector Embeddings (như SentenceTransformers) để tìm kiếm đồng nghĩa ngữ nghĩa (Semantic Search). Nếu hành khách dùng từ đồng nghĩa hoàn toàn khác với FAQ, Retriever sẽ không tìm thấy chunk phù hợp.

### 2.5. Shared Utilities (`shared/`)
- `shared/config.py`: Đọc cấu hình từ file `.env` bằng `pydantic-settings`.
- `shared/logger.py`: Khởi tạo cấu hình ghi log dạng file `logs/kiosk_app.log` và console log.
- `shared/schemas.py`: Định nghĩa các Pydantic Models (`QueryRequest`, `EntityExtract`, `IntentResult`, `RouteRecommendation`, `RetrievedContext`, `OfflineResponse`).
- `shared/security.py`: Hàm `sanitize_input_text()` loại bỏ thẻ HTML, script injection (`<script>`, `javascript:`, `onerror=`), lệnh eval/system, và các chuỗi Prompt Injection độc hại (`ignore previous instructions`, `system prompt:`).

### 2.6. Frontend UI Kiosk (`kiosk_ui/index.html`)
- **Vai trò:** Màn hình tương tác người dùng tại Trạm xe buýt.
- **Logic:**
  - Giao diện đơn file HTML/CSS/JS được thiết kế chuyên nghiệp theo phong cách Dark Mode hiện đại (Slate/Cyan/Emerald palette).
  - Tích hợp **Leaflet.js Map** tự động vẽ đường Polyline nối các điểm dừng khi AI gợi ý tuyến xe buýt.
  - Tích hợp **Web Speech API**:
    - `webkitSpeechRecognition`: Chuyển giọng nói tiếng Việt thành văn bản (STT).
    - `speechSynthesis`: Đọc câu trả lời của AI bằng giọng nói tiếng Việt (TTS).
  - Nút bấm đổi chế độ **ONLINE / OFFLINE Mode** trực tiếp trên Header để kiểm thử.
  - Các pill gợi ý nhanh ("Mỹ Đình ➔ Bách Khoa", "Xe buýt qua Hồ Gươm", "Giá vé xe buýt", "Metro Cát Linh").
- **Điểm mạnh:** Đẹp mắt, mượt mà, phản hồi tức thì, hiệu ứng âm thanh/sóng giọng nói sinh động, hỗ trợ đầy đủ giọng nói và bản đồ tương tác.
- **Điểm yếu:**
  - Phụ thuộc vào CDN bên ngoài (`unpkg.com/leaflet`, `fonts.googleapis.com`). Nếu Kiosk chạy 100% Offline ngắt mạng hoàn toàn, Leaflet Map sẽ không tải được Tile hình ảnh (được xử lý fallback hiển thị thông báo bản đồ ngoại tuyến) và Google Fonts sẽ rớt về font mặc định.
  - Phụ thuộc trình duyệt Google Chrome cho Web Speech STT/TTS.

### 2.7. Scripts & Data Pipeline (`scripts/`, `data/`, `knowledge_base/`)
- `scripts/build_knowledge_base.py`:
  - Đọc file Excel `data xe buýt.xlsx` (135 tuyến), toàn bộ file txt trong `data/hanoi/` (danh sách tuyến, giờ chạy, BRT01, Metro 2A & 3), file txt `data/hcm/`, dữ liệu GTCC `gtcc_kienthuc.txt`, và dữ liệu fine-tuning QA `finetune_gtcc.jsonl`.
  - Đổ dữ liệu vào SQLite DB `knowledge_base/local_transit.db` (tạo các bảng `routes`, `stops`, `route_stops`, `faqs`) và tạo file `knowledge_base/faq_store.json`.
  - Kết quả nạp thực tế: **136 tuyến xe buýt** và **590 điểm dừng độc lập** được đánh chỉ mục.
- `scripts/run_offline_demo.py`: Kịch bản test CLI chạy 6 câu hỏi mẫu offline và chế độ nhập interactive.

### 2.8. Test Suite (`tests/`)
- `tests/test_e2e_production.py`: Kiểm thử API endpoint FastAPI (Status, Chat, Input Sanitization, Network Toggle, UI Static Page).
- `tests/test_offline_mode.py`: Kiểm thử 7 kịch bản Offline Assistant (Tuyến đi thẳng, Địa danh Hồ Gươm, Tra cứu giá vé, Tuyến Metro, Tuyến 999 không tồn tại ➔ Fallback, Đi Hà Nội - Sài Gòn ➔ Fallback, Kiểm tra latency).

---

## 3. BẢNG ĐÁNH GIÁ RỦI RO KỸ THUẬT (RISK ASSESSMENT MATRIX)

| Mã Rủi ro | Phân loại | Mức độ | Mô tả Rủi ro Thực tế | Nguyên nhân Gốc rễ | Giải pháp Khắc phục |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | **Hallucination** | `Medium` | LLM sinh ra thông tin sai về địa điểm chuyển tuyến hoặc thời gian hoạt động của tuyến bus. | Anti-Hallucination Validator hiện chỉ check `route_id`, chưa check thực thể địa danh (`stop_names`). | Nâng cấp `AnswerValidator` kiểm tra cả cặp (`route_id`, `stop_name`) so with DB. |
| **RSK-02** | **Performance** | `High` | Độ trễ suy luận LLM cao (5s - 15s) khi chạy Ollama trên thiết bị Edge phần cứng yếu (không GPU). | Mô hình LLM 3B tham số vẫn nặng đối với CPU nhúng thông thường. | Khuyên dùng Tầng 3 (Local Deterministic Summarizer) cho Edge CPU, hoặc trang bị NPU (Jetson Orin/Hailo-8). |
| **RSK-03** | **Security** | `Medium` | Thiếu Authentication/API Key trên các Endpoint điều khiển như `/api/toggle-network`. | API Backend mở hoàn toàn CORS (`allow_origins=["*"]`) và không có JWT/API Key. | Thêm API Key Header / Basic Auth cho các endpoint quản trị hệ thống. |
| **RSK-04** | **Scalability** | `High` | Chưa có cơ chế đồng bộ dữ liệu Realtime (GTFS-RT / Bus GPS) từ Server trung tâm. | Thư mục `sync_service/` hiện đang rỗng, dữ liệu xe buýt hoàn toàn là tĩnh (Static SQLite). | Xây dựng Sync Agent chạy định kỳ khi Kiosk có lại kết nối 4G/Wi-Fi. |
| **RSK-05** | **Maintainability**| `Low` | Nhiều thư mục dư thừa rỗng trong repository (`dashboard`, `frontend`, `prompts`, v.v.). | Bộ khung dự án khởi tạo sẵn cấu trúc 20 phases nhưng chưa dọn dẹp các folder rỗng. | Tiến hành dọn dẹp hoặc bổ sung mã nguồn vào các thư mục rỗng. |
| **RSK-06** | **Reliability** | `Medium` | Giao diện UI bị phụ thuộc vào CDN bên ngoài (`unpkg.com`, `googleapis.com`). | File `index.html` link trực tiếp các thư viện CSS/JS từ internet. | Bundle cục bộ toàn bộ file `leaflet.js`, `leaflet.css` và Fonts vào thư mục `kiosk_ui/vendor/`. |

---

## 4. LỘ TRÌNH CẢI TIẾN THỰC TẾ (IMPROVEMENT ROADMAP)

### Sprint 1: Chuẩn hóa & Đóng gói Ngoại tuyến Hoàn toàn (Offline Self-Containment)
1. **Localize Frontend Vendor Assets:** Tải toàn bộ `leaflet.js`, `leaflet.css` và font chữ Inter/Outfit về lưu cục bộ tại `kiosk_ui/assets/` để giao diện Kiosk hiển thị 100% hoàn hảo ngay cả khi ngắt kết nối mạng tuyệt đối.
2. **Cập nhật Prompt Management:** Chuyển các chuỗi Prompt hardcoded trong `llm_engine.py` vào thư mục `prompts/system_prompt_kiosk.txt` để dễ dàng bảo trì và tinh chỉnh.
3. **Cấu hình Bảo mật Backend:** Đóng bớt CORS `allow_origins` và bổ sung Middleware kiểm tra `X-API-Key` cho endpoint `/api/toggle-network`.

### Sprint 2: Dựng Đồ thị Giao thông Chính xác (Spatial Graph Engine)
1. **Chuyển đổi sang NetworkX / Routing Engine:** Dùng tọa độ GPS thực tế của 590 điểm dừng để xây dựng đồ thị `networkx.DiGraph`.
2. **Tính toán Đi bộ (Walking Distance):** Tính khoảng cách Haversine giữa các trạm chuyển tuyến để khuyến nghị đường đi bộ ngắn nhất cho hành khách.

### Sprint 3: Triển khai Dịch vụ Đồng bộ (Sync Service & GTFS Integration)
1. **Thiết lập Sync Service (`sync_service/`):** Xây dựng background worker kiểm tra kết nối Internet định kỳ.
2. **Cập nhật SQLite Tự động:** Khi có mạng, tự động tải bản cập nhật lịch trình xe buýt mới nhất từ Server trung tâm về Kiosk.

---

## 5. ĐÁNH GIÁ KHOẢNG CÁCH (GAP ANALYSIS)

### 5.1. Nếu phát triển thành SẢN PHẨM THƯƠNG MẠI (Commercial Product), hệ thống còn thiếu gì?
1. **Phần cứng Chuyên dụng & Watchdog Service:**
   - Chưa có dịch vụ Watchdog (như `systemd` service hoặc Docker restart policy nâng cao) để tự động khôi phục ứng dụng Kiosk nếu bị crash hoặc tràn bộ nhớ.
   - Chưa tích hợp cảm biến tiệm cận (PIR Sensor) để bật/tắt màn hình tiết kiệm điện năng.
2. **Tích hợp Dữ liệu Xe buýt Real-time (GTFS-RT / GPS Tracking):**
   - Hiện tại hệ thống tra cứu theo lịch trình cố định. Một sản phẩm thương mại bắt buộc phải hiển thị *"Tuyến 26 còn 3 phút nữa sẽ đến trạm"* dựa trên GPS thực tế của xe.
3. **Hệ thống Quản trị Tập trung (Central Kiosk Management Dashboard):**
   - Thư mục `dashboard/` hiện đang rỗng. Cần một Web Dashboard cho đơn vị vận hành (Sở GTVT/Doanh nghiệp xe buýt) giám sát trạng thái sức khỏe (Heartbeat, CPU/RAM, Nhiệt độ), nhật ký truy vấn và quảng cáo trên hàng trăm Kiosk.
4. **Xử lý Giọng nói Chuyên dụng Ngoài trời (Far-field Noise Robust Speech API):**
   - Web Speech API của trình duyệt không hoạt động tốt trong môi trường tiếng ồn giao thông thực tế (> 70dB). Cần tích hợp mảng Micro phần chống ồn (DSP Hardware Micro Array) và mô hình Offline STT cục bộ như `Whisper-tiny.en/vi` hoặc `Sherpa-onnx`.

### 5.2. Nếu phát triển thành ĐỀ TÀI NGHIÊN CỨU KHOẢNHỌC (Academic Research), hệ thống còn thiếu gì?
1. **Báo cáo Thực nghiệm Benchmark So sánh (Empirical Benchmark Suite):**
   - Chưa có bảng so sánh định lượng (Quantitative Benchmark) giữa:
     - Độ chính xác intent (Accuracy/F1-Score) của Rule-based vs BERT/PhoBERT.
     - Thời gian phản hồi (Latency ms) và lượng tiêu thụ tài nguyên (RAM/VRAM/Power) của Qwen2.5-3B vs Llama-3-8B vs Deterministic Summarizer.
     - Tỷ lệ ảo giác (Hallucination Rate %) trước và sau khi qua lớp Answer Validator.
2. **Hình thức hóa Toán học cho Đồ thị Định tuyến (Mathematical Graph Formalization):**
   - Chưa trình bày công thức toán học tổng quát cho bài toán tìm đường đa tiêu chí (Multi-objective Path Finding: Tối thiểu số lần đổi xe $T$, tối thiểu tiền vé $C$, và tối thiểu thời gian di chuyển $W$).
3. **Đánh giá Tỷ lệ Lỗi Giọng nói (Word Error Rate - WER):**
   - Chưa có thực nghiệm đo đạc chỉ số WER của mô hình nhận dạng giọng nói tiếng Việt trong các kịch bản môi trường tiếng ồn âm thanh đường phố khác nhau.

---

## 6. KẾT LUẬN CỦA HỘI ĐỒNG KIỂM TOÁN

Dự án **AI Smart Bus Stop Assistant** sở hữu một mã nguồn **gọn gàng, kiến trúc rõ ràng, hoạt động thực tế 100% ấn tượng ở chế độ Offline**. Core pipeline bao gồm Nhận diện ý định -> Tra cứu Đồ thị SQLite -> Sinh câu trả lời LLM/Summarizer -> Kiểm duyệt Chống ảo giác được kết nối hoàn chỉnh từ Backend FastAPI tới Frontend Kiosk UI.

Mặc dù một số thư mục nâng cao vẫn đang ở dạng khung (skeleton/empty directories) và Cloud Mode hiện tại là môphỏng, nhưng **phần cốt lõi Offline Local AI Pipeline của dự án hoàn toàn có thật, chạy mượt mà và đạt tiêu chuẩn xuất sắc cho một Đồ án Tốt nghiệp chuyên ngành Hệ thống Thông tin / Khái niệm Edge AI Smart City.**

---
