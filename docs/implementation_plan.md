# MASTER IMPLEMENTATION PLAN: Offline AI Smart Bus Stop Assistant

Thưa Hội đồng, để đáp ứng tiêu chuẩn khắt khe (Engineering Standard, Self Review Loop, Quality Gate) cho hệ thống **Offline AI Smart Bus Stop Assistant**, tôi đã lập Kế hoạch Triển khai Tổng thể (Master Plan) chia 20 Phase thành 6 Sprint thực thi. Mặc dù chúng ta đã khởi tạo bộ khung cơ bản trước đó, nhưng với yêu cầu mới này, toàn bộ tài liệu và thiết kế sẽ được đập đi xây lại ở một cấp độ sâu sắc và hàn lâm hơn rất nhiều.

## Quy tắc Thực thi chung cho mọi Sprint
Mỗi Phase trong Sprint sẽ được thiết kế với chuẩn mực:
- **Cấu trúc Phase:** Objective, Input, Output, Dependencies, Deliverables, Risks, Acceptance Criteria.
- **Tiêu chuẩn Kỹ thuật:** Mọi quyết định đều phải có: Vì sao chọn? Thay thế? Ưu/Nhược điểm? Khi nào dùng/không dùng?
- **Self Review:** Review chéo (Cross-review) giữa các vai trò (Architect, AI Engineer, Security, v.v.) ở cuối mỗi Phase.
- **Tài liệu:** Cập nhật trực tiếp vào 15 file Markdown tương ứng trong `docs/`.

---

## 🏃 Lộ trình các Sprint

### SPRINT 1: Khởi tạo & Phân tích Yêu cầu (Phases 1 - 3)
- **Phase 1: Research** (Nghiên cứu thị trường Kiosk, giới hạn Edge AI).
- **Phase 2: Requirement Analysis** (Yêu cầu chức năng, phi chức năng, ranh giới Online/Offline).
- **Phase 3: Business Analysis** (User Persona, Pain points, Business/Scientific Value).
- **Tài liệu Output:** `PROJECT_OVERVIEW.md`, `REQUIREMENTS.md`.

### SPRINT 2: Kiến trúc & Nền tảng (Phases 4 - 7)
- **Phase 4: System Architecture** (Thiết kế tổng thể Hybrid).
- **Phase 5: Repository Initialization** (Rà soát lại cấu trúc thư mục hiện tại).
- **Phase 6: Folder Structure** (Chuẩn hóa vai trò từng module).
- **Phase 7: Technology Selection** (Quyết định stack công nghệ có đối chiếu ưu/nhược điểm).
- **Tài liệu Output:** `SYSTEM_ARCHITECTURE.md`, `README.md`.

### SPRINT 3: Phần cứng & AI Cục bộ (Phases 8 - 11)
- **Phase 8: Hardware Architecture** (Jetson vs Raspberry Pi, E-ink vs LCD).
- **Phase 9: Software Architecture** (OS, Containerization, Watchdog).
- **Phase 10: Edge AI** (AI Pipeline tại biên).
- **Phase 11: LLM** (Chọn model Quantized: Llama-3 vs Qwen vs Mistral).
- **Tài liệu Output:** `HARDWARE_DESIGN.md`, `SOFTWARE_DESIGN.md`, `EDGE_AI_ARCHITECTURE.md`.

### SPRINT 4: Tri thức & Giọng nói (Phases 12 - 14)
- **Phase 12: RAG** (Local Retrieval, VectorDB trên thiết bị nghèo tài nguyên).
- **Phase 13: Knowledge Base** (Chiến lược đồng bộ Delta).
- **Phase 14: Speech AI** (STT Whisper.cpp, TTS Piper, VAD, Lọc ồn).
- **Tài liệu Output:** `RAG_ARCHITECTURE.md`, `KNOWLEDGE_BASE.md`.

### SPRINT 5: Tích hợp Hệ sinh thái & Bảo mật (Phases 15 - 18)
- **Phase 15: Google Maps Integration** (Tích hợp API fallback khi có mạng).
- **Phase 16: Dashboard** (Hệ thống giám sát trạm tập trung).
- **Phase 17: API Design** (Đặc tả giao thức MQTT/gRPC).
- **Phase 18: Security** (Anti-Tampering, mTLS, LUKS).
- **Tài liệu Output:** `API_SPECIFICATION.md`, `SECURITY.md`, `UX_DESIGN.md`.

### SPRINT 6: Triển khai & Nghiệm thu (Phases 19 - 20)
- **Phase 19: Deployment** (Hướng dẫn lắp đặt, OTA).
- **Phase 20: Testing & Production Readiness** (Chaos Engineering, Hardware Stress Test, Production Checklist).
- **Tài liệu Output:** `DEPLOYMENT_GUIDE.md`, `TEST_PLAN.md`, `ROADMAP.md`, `RISKS.md`, `CHANGELOG.md`.

---

## 🚦 Quality Gate (Yêu cầu Phê duyệt)
Vì dự án làm việc theo tiêu chí **"Không ưu tiên tốc độ, ưu tiên chính xác và có thể triển khai"**, tôi sẽ dừng lại sau mỗi Sprint để chờ phản hồi từ bạn.

> [!IMPORTANT]
> **Hỏi ý kiến người dùng:** 
> Bạn có đồng ý với Lộ trình 6 Sprint trên không? Nếu đồng ý, xin hãy cấp quyền, tôi sẽ lập tức bắt đầu chạy **Sprint 1 (Phases 1, 2, 3)**, viết lại toàn bộ `PROJECT_OVERVIEW.md` và `REQUIREMENTS.md` đạt tiêu chuẩn luận án Tiến sĩ / Enterprise Architecture Blueprint.
