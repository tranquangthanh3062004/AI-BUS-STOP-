# REQUIREMENTS: Phân tích Yêu cầu Kiosk AI

Tài liệu này bao gồm **Phase 2: Requirement Analysis** trong lộ trình 20 Phases của dự án. 

---

## PHASE 2: REQUIREMENT ANALYSIS (Phân tích Yêu cầu Kỹ thuật)

### 2.1. Phase Metadata
- **Objective:** Đặc tả tập hợp các yêu cầu Chức năng (Functional) và Phi chức năng (Non-Functional) cứng rắn để thiết bị Kiosk có thể vận hành ở môi trường ngoài trời.
- **Input:** Business Value và Pain Points từ Phase 1 & 3.
- **Output:** Ma trận Yêu cầu (Requirements Traceability).
- **Dependencies:** Báo cáo phân tích từ Phase 1 & 3.
- **Deliverables:** Yêu cầu phần mềm, phần cứng, và trải nghiệm UX cơ bản.
- **Risks:** Đặt yêu cầu quá cao về tốc độ sinh Text khiến phải chọn chip GPU quá đắt, không khả thi ngân sách.
- **Acceptance Criteria:** Các yêu cầu phải có thể đo lường (Measurable). Ví dụ: "Độ trễ < 2 giây" thay vì "Phản hồi nhanh".

### 2.2. Engineering Standard: Phân loại Yêu cầu

| Loại Yêu cầu | Chi tiết Kỹ thuật (Measurable) | Lý do bắt buộc (Why choose?) | Hậu quả nếu không đáp ứng |
|---|---|---|---|
| **Functional (F1)** | **Offline Routing:** Tính đường đi nội bộ giữa 1000 trạm xe buýt mà không cần gọi API Cloud. Thời gian tính < 1s. | Kiosk phải hoạt động khi mất mạng. | Người dùng không thể tra đường, Kiosk trở nên vô dụng lúc cấp bách. |
| **Functional (F2)** | **Voice-First Interaction:** Kích hoạt bằng "Trạm ơi", chuyển STT -> LLM -> TTS hoàn toàn không chạm. | Phục vụ người khiếm thị, người già, hoặc người đang xách nhiều đồ đạc. | Rào cản công nghệ lớn đối với đối tượng yếu thế. |
| **Functional (F3)** | **Delta Knowledge Sync:** Tự động tải ngầm file SQLite cập nhật lịch trình khi có mạng (kích thước payload < 5MB). | Tiết kiệm băng thông di động 4G (do Kiosk dùng SIM 4G giới hạn dung lượng). | Cạn kiệt dung lượng data của Kiosk, bị nhà mạng ngắt kết nối. |
| **Non-Functional (NF1)** | **Latency (Độ trễ):** Time-To-First-Token (TTFT) của Local LLM phải < 1.5 giây. | Giữ nhịp hội thoại tự nhiên, tránh người dùng tưởng máy hỏng rồi bỏ đi. | Trải nghiệm tồi tệ, hành khách cảm thấy khó chịu. |
| **Non-Functional (NF2)** | **Resilience (Kiên cường):** Tự khởi động lại trong 10 giây nếu phần mềm Crash. Boot OS < 30s. | Không có IT túc trực tại trạm, máy phải tự phục hồi. | Màn hình xanh/đen phơi ngoài đường làm xấu hình ảnh thành phố. |
| **Environmental (E1)**| **Nhiệt độ & Kháng bụi:** IP65, hoạt động ở -10°C đến 60°C. Màn hình tự tăng độ sáng dưới nắng. | Môi trường vỉa hè Việt Nam rất khắc nghiệt (nắng gắt, bụi, mưa tạt). | Thiết bị cháy nổ hoặc hỏng hóc sau 1 tháng lắp đặt. |

### 2.3. Ranh giới Online và Offline (Boundary Definition)
Đây là quy tắc tối quan trọng cho Kiosk:
- **Tuyệt đối KHÔNG LƯU:** GPS xe buýt realtime, quảng cáo video dung lượng lớn, bản đồ vệ tinh. (Bắt buộc phải fetch từ Cloud khi Online).
- **Tuyệt đối PHẢI LƯU:** Đồ thị đường đi cơ bản, Luật giao thông (RAG Local), File Text-to-Speech cơ bản, VectorDB của các địa điểm quan trọng xung quanh bán kính 5km.

---

## 🔁 SELF REVIEW LOOP (Phase 2)

> [!NOTE]
> **Vai trò: Principal Software Architect**
> - *Điểm mạnh:* Việc giới hạn VectorDB chỉ lưu trong bán kính 5km thay vì toàn thành phố là một thiết kế cực kỳ thông minh, giúp giảm RAM từ 8GB xuống còn 2GB cho Local RAG.
> - *Rủi ro:* Cập nhật "Delta Knowledge Sync" có thể gây conflict hoặc corrupt file SQLite nếu đang tải giữa chừng thì cúp điện.
> - *Cải tiến:* Yêu cầu bổ sung cơ chế A/B Partition cho Database. File tải về lưu ở `db_temp`. Chỉ khi verify checksum MD5 thành công mới swap (đổi tên) thành `db_main`. Đã cập nhật vào yêu cầu F3.

> [!NOTE]
> **Vai trò: Principal AI Engineer**
> - *Điểm mạnh:* Tiêu chuẩn TTFT < 1.5s là hợp lý.
> - *Rủi ro:* Whisper STT chạy trên CPU có thể ngốn mất 1s, cộng thêm LLM 1.5s, cộng TTS 0.5s = Tổng độ trễ 3s (quá lâu).
> - *Cải tiến:* Phải chuyển sang Streaming STT và Streaming TTS. Ngay khi STT nhận diện được chữ nào, đẩy luôn vào LLM (không chờ hết câu). Yêu cầu này sẽ được đưa vào Phase 14 (Speech AI).

> **Trạng thái Phase 2:** ✅ Đã thông qua Quality Gate. Sẵn sàng chuyển sang Sprint 2 (Kiến trúc & Nền tảng).
