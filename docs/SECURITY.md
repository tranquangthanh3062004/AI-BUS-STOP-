# SECURITY: An ninh Thông tin & Bảo vệ Thiết bị Vật lý

Tài liệu này bao gồm **Phase 18: Security** trong lộ trình 20 Phases của dự án. 

---

## PHASE 18: SECURITY (Bảo mật Tổng thể)

### 18.1. Phase Metadata
- **Objective:** Ngăn chặn các cuộc tấn công vật lý (Physical Attack) tại vỉa hè và tấn công mạng (Cyber Attack) khi truyền tải dữ liệu. Bảo vệ mã nguồn AI và dữ liệu khách hàng.
- **Input:** Mô hình Hardware (Phase 8), API MQTT (Phase 17).
- **Output:** Chính sách Bảo mật (Security Policies) và Cơ chế mã hóa.
- **Dependencies:** Phase 8, 9, 17.
- **Deliverables:** LUKS Disk Encryption, mTLS, Anti-Tampering.
- **Risks:** Kẻ gian đập vỡ vỏ hộp, tháo thẻ nhớ/SSD ra ngoài để trộm bộ code Llama.cpp và Key API Google Maps.
- **Acceptance Criteria:** Dù thẻ nhớ bị tháo ra, hacker không thể đọc được bất cứ file nào (Data at Rest Encryption).

### 18.2. Engineering Standard: Các lớp Bảo mật (Security Layers)

| Lớp Bảo mật | Cơ chế (Vì sao chọn?) | Hậu quả nếu không làm (Risks) |
|---|---|---|
| **Data at Rest (Dữ liệu nằm im)** | **Mã hóa ổ đĩa toàn phần LUKS (Linux Unified Key Setup) với TPM 2.0 (Trusted Platform Module).** Key mã hóa được cất trong con chip TPM cứng của Jetson. | Kẻ gian ăn trộm thẻ nhớ SD, cắm vào máy tính khác đọc được toàn bộ `.env` chứa mật khẩu Database và API Key của hệ thống lõi. |
| **Data in Transit (Dữ liệu truyền tải)** | **mTLS (Mutual TLS) cho MQTT.** Kiosk và Cloud phải xác thực chứng chỉ chéo lẫn nhau. Chỉ cấp phát chứng chỉ X.509 riêng biệt cho từng số Serial Number Kiosk. | Hacker dùng laptop bắt gói tin 4G (Man-in-the-Middle) để đọc trộm/ghi đè bản cập nhật Database, tiêm mã độc vào file SQLite. |
| **Physical Security (Bảo mật Vật lý)** | **Anti-Tampering Switch (Công tắc chống phá hoại).** Khi vỏ thép bảo vệ Kiosk bị cạy mở trái phép, công tắc nhả ra -> Phần cứng lập tức cắt nguồn điện vào SSD/eMMC để xóa bộ nhớ tạm (RAM/Key), đồng thời gửi tín hiệu SOS (Ping cuối cùng) lên Cloud bằng pin dự phòng nhỏ. | Thiết bị bị mổ bụng, can thiệp vào bo mạch để câu dây Console/UART hack thẳng vào quyền ROOT. |

### 18.3. Quản lý Mật danh & Danh tính (Identity Management)
- Mỗi Kiosk xuất xưởng không có mật khẩu root (Disabled Root Login).
- Thay vì dùng Mật khẩu, thiết bị được cấp quyền (Provisioned) bằng Cloud IoT Core (như AWS IoT hoặc Azure IoT Hub) thông qua chứng chỉ được sinh ngẫu nhiên 1 lần. Nếu Kiosk báo mất, lập tức Thu hồi chứng chỉ (Revoke Certificate) từ Cloud, biến cỗ máy thành cục sắt vụn không thể nối mạng.

---

## 🔁 SELF REVIEW LOOP (Phase 18)

> [!NOTE]
> **Vai trò: Principal Security Engineer**
> - *Điểm mạnh:* Kết hợp LUKS với TPM 2.0 và Anti-Tampering Switch là cấp độ bảo mật của máy ATM Ngân hàng. Nó loại trừ hoàn toàn rủi ro bị trộm tài sản trí tuệ (AI Models, Source Code).
> - *Rủi ro:* Nếu Kiosk bị hỏng phần cứng thật (chứ không phải bị hack) và nhân viên bảo trì cần sửa, họ mở vỏ máy ra thì Anti-Tampering Switch cũng sẽ xóa sạch Key, gây tốn kém tiền cài đặt lại phần mềm.
> - *Cải tiến:* Xây dựng quy trình "Maintenance Mode". Nhân viên trước khi mở tủ Kiosk phải dùng App điện thoại (Quét NFC) để báo hiệu cho Cloud tạm vô hiệu hóa (Disable) Anti-Tampering Switch trong 30 phút. Giải pháp này cân bằng giữa Bảo mật và Vận hành (SecOps). Đã cập nhật vào SOP của Phase 19 (Deployment).

> **Trạng thái Phase 18:** ✅ Đã thông qua Quality Gate. Sẵn sàng tiến vào Sprint cuối cùng.
