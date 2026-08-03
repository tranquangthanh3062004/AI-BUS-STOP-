# HARDWARE ARCHITECTURE: Thiết kế Phần cứng Kiosk

Tài liệu này bao gồm **Phase 8: Hardware Architecture** trong lộ trình 20 Phases của dự án. 

---

## PHASE 8: HARDWARE ARCHITECTURE (Kiến trúc Phần cứng)

### 8.1. Phase Metadata
- **Objective:** Xác định tổ hợp linh kiện vật lý đáp ứng được cường độ xử lý AI nội bộ, chịu được môi trường ngoài trời khắc nghiệt, và tiết kiệm điện.
- **Input:** Báo cáo Kiến trúc lai (Phase 4). Yêu cầu độ trễ < 1.5s (Phase 2).
- **Output:** Sơ đồ Block linh kiện vật lý (Bo mạch, SoC, Màn hình, Cảm biến, UPS).
- **Dependencies:** Phase 4.
- **Deliverables:** Hardware Bill of Materials (BOM) sơ bộ.
- **Risks:** Nhiệt lượng tỏa ra từ NPU khi chạy LLM liên tục làm quá nhiệt thiết bị (Thermal Throttling) dẫn đến Crash.
- **Acceptance Criteria:** Phần cứng phải có Thermal Design Power (TDP) < 30W và đủ RAM (>= 8GB) để chứa Llama-3-8B (Q4).

### 8.2. Engineering Standard: Lựa chọn Module Xử lý Trung tâm (SoC/SBC)

| SoC / Mạch nhúng | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **NVIDIA Jetson Orin Nano (8GB)** | **(Lựa chọn chính thức)**. Sở hữu kiến trúc Ampere với 1024 CUDA Cores và 32 Tensor Cores. Đạt hiệu suất LLM 15-20 token/s. | Raspberry Pi 5 + Google Coral TPU | Khả năng tương thích AI cực tốt (hỗ trợ TensorRT bản native). Chạy được cả LLM và Whisper STT song song. | Giá thành khá cao (~$299). Cần tản nhiệt chủ động (quạt). | Khi chỉ cần hiển thị màn hình LED tĩnh (Không cần AI). |
| **Raspberry Pi 5 (8GB)** | Bị loại bỏ. Vì Coral TPU của Google chỉ hỗ trợ mô hình TFLite siêu nhỏ (Vision/Object Detection), không có bộ nhớ (VRAM) đủ lớn để load tham số LLM hàng GB. | Jetson Nano 4GB (Đời cũ) | Giá rất rẻ (~$80), dễ mua. Tiết kiệm điện. | Chạy LLM bằng CPU ARM cực chậm (~2-3 tokens/s). Không đáp ứng chuẩn TTFT < 1.5s. | Bắt buộc loại bỏ cho dự án dùng Generative AI Local. |

### 8.3. Engineering Standard: Màn hình & Tương tác

| Linh kiện | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **Màn hình E-Ink 32"** | **(Lựa chọn chính thức)**. Thiết kế theo tiêu chí "Voice-first". Màn hình chỉ dùng để vẽ Bản đồ tĩnh và thông số xe buýt (Refresh rate thấp). Tiêu thụ điện 0W khi tĩnh. | Màn hình LCD High-Brightness | Đọc rất rõ dưới ánh nắng gắt. Tiết kiệm cực lớn năng lượng. Không bị chói/lóa (Glare). | Tần số quét quá chậm (1Hz), không thể xem Video. Chỉ hiển thị trắng đen (hoặc 3 màu cơ bản). | Khi điểm dừng là khu phức hợp cần phát quảng cáo Video 4K kiếm tiền (Ad-Tech). (Lúc đó mới cân nhắc LCD). |
| **Microphone Array (4-Mic) DSP** | Bắt buộc có phần cứng tích hợp DSP (Digital Signal Processing). | Micro USB bình thường | Lọc tiếng còi xe (Noise Cancellation), lọc tiếng gió (Wind Shield), Định hướng chùm âm thanh (Beamforming). | Đắt tiền, cần cấu hình ALSA/PulseAudio phức tạp trên Linux. | - |

---

## 🔁 SELF REVIEW LOOP (Phase 8)

> [!NOTE]
> **Vai trò: Principal Intelligent Transportation Systems (ITS) Engineer**
> - *Điểm mạnh:* Việc chọn Màn hình E-Ink 32 inch là quyết định đột phá, mang lại cảm giác thân thiện với môi trường (Eco-friendly) và giải quyết triệt để bài toán Kiosk bị "đen ngòm" khi chói nắng.
> - *Rủi ro:* Màn hình E-ink nếu bị vỡ/nứt do phá hoại (Vandalism) thì chi phí thay thế đắt hơn LCD nhiều lần.
> - *Cải tiến:* Yêu cầu bọc một lớp Kính Cường Lực (Tempered Glass IK10) dày 8mm phủ lớp chống lóa (Anti-glare coating) bên ngoài màn hình E-ink. Cấu trúc giá đỡ thép (Steel Enclosure) chống gỉ sét.

> [!NOTE]
> **Vai trò: Principal Security Engineer**
> - *Rủi ro:* Cổng USB trên Jetson Orin Nano nếu phơi ra ngoài, hacker có thể cắm bàn phím vào và xâm nhập hệ điều hành.
> - *Cải tiến:* Bịt kín 100% cổng USB bằng keo Epoxy. Loại bỏ hoặc vô hiệu hóa cổng Ethernet/USB vật lý trên phần cứng (Hardware-level disablement). Đã bổ sung thiết kế này vào bản vẽ.

> **Trạng thái Phase 8:** ✅ Đã thông qua Quality Gate. 
