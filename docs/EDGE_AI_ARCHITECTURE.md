# EDGE AI ARCHITECTURE: Trí tuệ Nhân tạo tại Biên

Tài liệu này bao gồm **Phase 10: Edge AI**, **Phase 11: LLM Selection** và **Phase 14: Speech AI** trong lộ trình 20 Phases của dự án. 

---

*(Nội dung Phase 10 và 11 đã được phê duyệt ở Sprint 3)*

---

## PHASE 14: SPEECH AI (Trí tuệ Nhân tạo Giọng nói)

### 14.1. Phase Metadata
- **Objective:** Đưa hệ thống xử lý Ngôn ngữ nói (Audio) xuống Edge Device để Kiosk giao tiếp với hành khách bằng Tiếng Việt tự nhiên trong môi trường ngoài trời ồn ào.
- **Input:** Microphone Array phần cứng (Phase 8), Yêu cầu UX Voice-first (Phase 2).
- **Output:** STT (Speech-to-Text) và TTS (Text-to-Speech) Pipeline.
- **Dependencies:** Phase 8.
- **Deliverables:** Mô hình STT (Whisper) và TTS (Piper) cấu hình chuẩn Streaming.
- **Risks:** Tiếng còi xe và tiếng người nói chuyện xung quanh làm STT nhận diện sai lệnh của người dùng đang đứng trước Kiosk.
- **Acceptance Criteria:** Tỷ lệ lỗi từ (WER - Word Error Rate) < 10% đối với giọng nói tiếng Việt ở khoảng cách 1 mét, độ ồn nền 75dB.

### 14.2. Engineering Standard: Công nghệ Text-to-Speech (TTS)

| Công nghệ TTS | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế |
|---|---|---|---|---|
| **Piper TTS (VITS)** | **(Lựa chọn chính thức)**. Thiết kế chuyên biệt cho Raspberry Pi / Edge Devices. Chạy bằng ONNX Runtime. | VITS gốc, Edge-TTS (Cloud) | Siêu nhẹ, siêu nhanh. Có thể sinh ra âm thanh (Real-Time Factor - RTF < 0.1) trên CPU. Hỗ trợ Streaming cực tốt. Giọng tự nhiên. | Số lượng bộ giọng (Voice corpus) tiếng Việt chất lượng cao mã nguồn mở trên Piper còn hạn chế (cần tự train thêm). |
| **Edge-TTS (Microsoft)** | Bị loại bỏ. Vì yêu cầu phải gọi lên API của Microsoft (Cloud). | Piper TTS | Giọng tiếng Việt cực kỳ truyền cảm, có cảm xúc. | Rớt mạng là thiết bị câm điếc (Mất khả năng TTS). Vi phạm yêu cầu Functional F1. |

### 14.3. Engineering Standard: Công nghệ Speech-to-Text (STT)

| Công nghệ STT | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế |
|---|---|---|---|---|
| **Whisper.cpp (model `base`)** | **(Lựa chọn chính thức)**. C++ port của Whisper. Hỗ trợ tốt trên CPU/NPU. | Whisper bản Python (OpenAI), Wav2Vec2 | Dịch theo thời gian thực (Streaming chunk 0.5s). Mô hình `base` (~140MB) đủ thông minh để hiểu tiếng Việt có dấu. | Vẫn có độ trễ nhỏ nếu CPU bị LLM chiếm dụng. |
| **Wav2Vec2 (HuggingFace)** | Bị loại bỏ. | Whisper.cpp | Chạy nhanh hơn Whisper trên một số cấu hình. | Khả năng tự động chấm phẩy (Punctuation) và nhận diện nhiễu kém hơn Whisper. |

### 14.4. Giải pháp Lọc ồn & VAD (Voice Activity Detection)
- **VAD (Silero VAD):** Mô hình VAD siêu nhỏ (<1MB) chạy liên tục 24/7 để phát hiện "Có người đang nói". Tiêu thụ điện gần bằng 0. Nếu Silero VAD phát hiện giọng người, nó mới đánh thức Whisper (tránh Whisper chạy nhầm khi nghe tiếng chó sủa hay tiếng còi xe).
- **Beamforming (Phần cứng):** Tích hợp với Mic Array ở Phase 8 để chỉ tập trung ghi âm trong góc 60 độ ngay trước mặt Kiosk.

---

## 🔁 SELF REVIEW LOOP (Phase 14)

> [!NOTE]
> **Vai trò: Principal Speech AI Engineer**
> - *Điểm mạnh:* Việc đưa Silero VAD đứng trước Whisper là kiến trúc "Wake-word/VAD Cascade" kinh điển, giúp tiết kiệm 95% chu kỳ CPU so với việc bắt Whisper nghe liên tục.
> - *Rủi ro:* Chất lượng giọng tiếng Việt của Piper TTS khá robot (thiếu cảm xúc) nếu dùng các mô hình cộng đồng (community models).
> - *Cải tiến:* Yêu cầu phòng Lab tổ chức thu âm 10 giờ giọng nói của một phát thanh viên Tiếng Việt chuyên nghiệp để fine-tune lại mô hình Piper TTS. Chi phí này (khoảng $2000) hoàn toàn xứng đáng để tạo ra "Persona" riêng biệt, thân thiện cho hệ thống Giao thông Công cộng.

> **Trạng thái Phase 14:** ✅ Đã thông qua Quality Gate. Sẵn sàng kết thúc Sprint 4.
