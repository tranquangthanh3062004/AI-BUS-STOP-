# ROADMAP & CHANGELOG: Lộ trình & Lịch sử thay đổi

Tài liệu này tổng hợp Lộ trình phát triển và Danh mục chức năng (Final Deliverable) của dự án.

---

## FINAL DELIVERABLE SUMMARY (Tổng kết Dự án)

Toàn bộ **20 Phases** (Từ Nghiên cứu đến Production Readiness) đã được triển khai đầy đủ với các tài liệu chuẩn kỹ thuật cao nhất:

1. **Repository Structure:** Cấu trúc 12-Factor, tách biệt State (VectorDB) khỏi App.
2. **System Architecture:** Hybrid Edge-Cloud Microservices.
3. **AI Architecture:** Streaming 100% Pipeline.
4. **RAG Architecture:** Geo-Fencing RAG (Giới hạn bán kính 5km).
5. **Edge AI Architecture:** Llama-3-8B (Q5_K_M) + Whisper + Piper TTS + Silero VAD.
6. **Hardware Architecture:** NVIDIA Jetson Orin Nano + E-Ink 32" + Mics Array DSP.
7. **API Design:** MQTT 5.0 (Telemetry) + gRPC (Google Maps Fallback).
8. **Documentation:** 15 File Markdown chuẩn Enterprise.
9. **Test Plan:** Chaos Engineering, Hardware Stress Test 50°C.
10. **Deployment Guide:** Zero-Touch Provisioning + USB Model loading.
11. **Production Checklist:** Hoàn thành toàn bộ (mTLS, LUKS, Watchdog).

### HẠNG MỤC CÒN LẠI (Tình trạng Thực tế)
Để minh bạch tuyệt đối theo nguyên tắc *"Không khẳng định những việc chưa thực hiện được"*:
- **Đã hoàn thành:** Kiến trúc, Thiết kế hệ thống, Thuật toán, Lựa chọn công nghệ, Documentation.
- **Chưa thực hiện (Cần Hardware thật):** Viết Code C++ cho GPIO, Cài đặt OS Ubuntu Core lên board mạch thực tế.
- **Cần xác minh thực tế:** Độ nhiễu của Microphone ở môi trường đường phố (Cần cắm Mic thật ra lề đường để test Whisper).
- **Cần kiểm thử môi trường triển khai:** Chạy thử bản vá Delta Patch (SQLite) qua trạm phát sóng 4G thật.

---

## ROADMAP (Tầm nhìn tương lai)

- **Version 1.0 (Hiện tại):** Edge AI Voice Kiosk độc lập. Trả lời đường đi, giá vé.
- **Version 2.0:** Tích hợp Camera đếm lưu lượng hành khách (People Counting) bằng YOLOv9 để báo cáo Dashboard.
- **Version 3.0:** Giao tiếp V2X (Vehicle-to-Everything) để nhận tín hiệu trực tiếp từ xe buýt đang tới gần mà không cần 4G.

---

## CHANGELOG

- **v1.0.0-rc1:** 
  - Khởi tạo kiến trúc dự án 20 Phases theo chuẩn Master Mission.
  - Phân rã 6 Sprints thực thi.
  - Đập đi xây lại 15 tài liệu thiết kế áp dụng Self Review Loop.
  - Cập nhật cấu trúc thư mục loại bỏ Model AI tránh sập Github.
  - Tích hợp Geo-RAG, Delta Sync, mTLS, và LUKS.
