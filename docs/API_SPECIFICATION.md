# API SPECIFICATION: Tích hợp Hệ sinh thái & Đặc tả Giao thức

Tài liệu này bao gồm **Phase 15: Google Maps Integration** và **Phase 17: API Design** trong lộ trình 20 Phases của dự án. 

---

## PHASE 15: GOOGLE MAPS INTEGRATION (Tích hợp Dịch vụ Bản đồ)

### 15.1. Phase Metadata
- **Objective:** Tận dụng dữ liệu thời gian thực (Real-time Transit) của Google Maps khi Kiosk đang có kết nối 4G ổn định, nhằm cung cấp ETA (thời gian đến) chính xác nhất.
- **Input:** Biến trạng thái `OFFLINE_MODE` của hệ thống.
- **Output:** Module Fallback chuyển đổi liền mạch giữa Bản đồ Cục bộ (Local) và Google Maps.
- **Dependencies:** API Key từ Google Maps Platform.
- **Deliverables:** Thuật toán Routing kép (Dual Routing Algorithm).
- **Risks:** Lượt gọi API Google Maps (Places/Directions) vượt quá hạn mức (Quota), gây phát sinh chi phí hàng nghìn USD.
- **Acceptance Criteria:** Kiosk KHÔNG BAO GIỜ gọi Google Maps API để render bản đồ nền (Base map) tĩnh. Chỉ gọi khi cần ETA hoặc khi `OFFLINE_MODE=False` và khách hỏi địa điểm xa ngoài 5km.

### 15.2. Thuật toán Routing Kép (Dual Routing)
Cơ chế hoạt động khi hành khách hỏi "Làm sao để đi từ đây tới Suối Tiên?":
1. **Bước 1 (Check Network):** Đọc cờ `OFFLINE_MODE` từ Redis.
2. **Bước 2 (Local First):** Luôn luôn truy vấn VectorDB và Đồ thị nội bộ trước. Nếu Suối Tiên nằm trong bán kính 5km, LLM sinh câu trả lời dựa trên dữ liệu nội bộ. Kết thúc.
3. **Bước 3 (Cloud Fallback):** Nếu Suối Tiên cách xa > 5km VÀ có mạng, Backend Kiosk sẽ gói tọa độ gửi qua MQTT lên Cloud. Cloud gọi API Google Directions, lấy JSON kết quả trả về Kiosk qua MQTT. Kiosk đọc kết quả cho hành khách. Nếu KHÔNG có mạng, LLM xin lỗi hành khách: *"Xin lỗi, Suối Tiên nằm ngoài phạm vi dữ liệu ngoại tuyến và trạm đang mất mạng"*.

*(Kiến trúc này giúp tiết kiệm 90% chi phí API so với việc gọi trực tiếp từ Kiosk).*

---

## PHASE 17: API DESIGN (Đặc tả Giao thức)

### 17.1. Phase Metadata
- **Objective:** Chuẩn hóa giao thức truyền tải Telemetry (Trạng thái thiết bị) từ hàng nghìn Kiosk lên Cloud (Dashboard).
- **Input:** Yêu cầu Băng thông thấp (Phase 4).
- **Output:** Danh sách Topic MQTT và Schema tin nhắn.
- **Risks:** Hàng nghìn thiết bị cùng lúc đẩy dữ liệu vào MQTT Broker gây sập hệ thống (Thundering Herd Problem).
- **Acceptance Criteria:** Kiosk phải phân tán ngẫu nhiên thời gian gửi Telemetry (Jittering từ 1-5 giây).

### 17.2. Engineering Standard: Lựa chọn Giao thức (Protocol Selection)

| Giao thức | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **MQTT 5.0** | **(Lựa chọn chính thức)**. Thiết kế chuyên biệt cho IoT. Cờ QoS=1 đảm bảo Cloud chắc chắn nhận được lỗi phần cứng của Kiosk ngay cả khi mạng rớt liên tục. | HTTP/REST | Header cực nhỏ (2 bytes). Có khái niệm LWT (Last Will and Testament) báo tử Kiosk khi mất điện đột ngột. | Hướng sự kiện (Event-driven) nên code phức tạp hơn API gọi-đáp (Req-Res) thông thường. | Không dùng để truyền tải file âm thanh STT. |
| **gRPC** | Dùng riêng cho việc Kiosk mượn Cloud gọi Google Maps API (cần tốc độ tức thì và kết quả trả về trực tiếp). | WebSockets | Serialize/Deserialize bằng Protobuf cực nhanh. | Khó debug qua terminal (không đọc được bằng curl thuần). | - |

### 17.3. Đặc tả MQTT Topic (MQTT Topic Schema)
- `kiosk/+/telemetry/health`: Báo cáo RAM, Nhiệt độ CPU, Nguồn điện mặt trời (Gửi mỗi 5 phút).
- `kiosk/+/telemetry/usage`: Báo cáo số lần hành khách tương tác (Ẩn danh, dùng cho Business Value).
- `kiosk/+/command/reboot`: Cloud ép Kiosk khởi động lại (QoS=2).
- LWT Topic: `kiosk/+/status` (Payload: `offline`). Nếu Kiosk sập nguồn, MQTT Broker tự động nhả tin nhắn này cho Dashboard.

---

## 🔁 SELF REVIEW LOOP (Phases 15 & 17)

> [!NOTE]
> **Vai trò: Principal Google Maps Platform Engineer**
> - *Điểm mạnh:* Việc khóa Google Maps Base Map (không tải gạch bản đồ - map tiles) tiết kiệm hàng núi tiền API, tuân thủ nghiêm ngặt bài toán Business (Tối ưu chi phí B2G).
> - *Rủi ro:* Kiosk mượn Cloud gọi Directions API, nếu Cloud bị sập (DDoS), tính năng dẫn đường xa sẽ tê liệt.
> - *Cải tiến:* Yêu cầu thiết lập Rate Limiting (Giới hạn truy cập) cho mỗi Kiosk ID ở API Gateway trên Cloud. Ngăn chặn trường hợp 1 Kiosk bị hack và spam hàng triệu request lên Cloud. Đã cập nhật.

> **Trạng thái Phase 15 & 17:** ✅ Đã thông qua Quality Gate.
