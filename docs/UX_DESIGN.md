# UX DESIGN & DASHBOARD: Trải nghiệm & Giám sát

Tài liệu này bao gồm **Phase 16: Dashboard** và chuẩn hóa UX tổng thể trong lộ trình 20 Phases.

---

## PHASE 16: DASHBOARD & UX (Hệ thống Giám sát & Trải nghiệm Trạm)

### 16.1. Phase Metadata
- **Objective:** (1) Thiết kế giao diện cho hành khách đứng tại Kiosk (UX), và (2) Thiết kế Bảng điều khiển trung tâm (Dashboard) cho nhân viên Sở GTVT theo dõi hàng nghìn Kiosk.
- **Input:** Khả năng phần cứng (Màn hình E-Ink), Business Value (Ad-Tech).
- **Output:** Luồng trạng thái Màn hình Kiosk, Các Metrics của Dashboard.
- **Dependencies:** API Specification (Phase 17).
- **Deliverables:** Ma trận trạng thái giao diện (UI State Machine).
- **Risks:** Giao diện Dashboard (Web) tải hàng ngàn Kiosk cùng lúc làm treo trình duyệt của nhân viên điều hành.
- **Acceptance Criteria:** Kiosk UI phải thân thiện với E-Ink (Không animation màu mè). Dashboard phải sử dụng WebSockets để nhận cảnh báo hỏng hóc (LWT) theo thời gian thực (Real-time).

### 16.2. Engineering Standard: Trải nghiệm Kiosk UI (Passenger-Facing)

| Thiết kế UX | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **High-Contrast (Độ tương phản cực cao)** | **(Lựa chọn chính thức)**. E-Ink chỉ có Đen/Trắng, cần phông chữ to (San Francisco / Roboto), nền trắng chữ đen đậm. Loại bỏ mọi Gradient và Đổ bóng. | Neumorphism / Glassmorphism | Đọc cực rõ, hỗ trợ người khiếm thị một phần. Tiết kiệm mực điện tử. | Trông hơi "cổ điển" (Retro), kém màu sắc. | Trên màn hình LCD 4K (lúc đó nên dùng thiết kế hiện đại). |
| **Giao diện dựa trên Trạng thái (State-driven)** | Màn hình tự động thay đổi dựa trên PIR Sensor (Cảm biến tiệm cận). | Giao diện tĩnh liên tục | Không có người: Hiển thị Bản đồ tĩnh + Biển quảng cáo (Tiết kiệm điện). Có người bước tới (<1m): Lập tức chuyển sang "Listening Mode" (Logo micro to giữa màn hình). | Yêu cầu phải lập trình hardware GPIO đọc PIR sensor siêu nhạy. | - |

### 16.3. Kiến trúc Central Dashboard (Control Room)
Bảng điều khiển trên Cloud phục vụ 2 nhóm:
1. **IT Support:** 
   - Bản đồ nhiễu nhiệt (Heatmap) hiển thị Kiosk nào đang offline/chết nguồn (Dựa vào LWT MQTT).
   - Nút `Force Reboot` (gửi lệnh xuống Kiosk).
   - Đồ thị theo dõi Thermal (Nhiệt độ SoC Jetson).
2. **Business / Marketing:**
   - Thống kê (Aggregated Data) luồng hành khách tiếp cận mỗi trạm trong ngày (được báo cáo ẩn danh từ Kiosk).
   - Nút phân phối Quảng cáo tĩnh (Push E-ink Ads) xuống hàng loạt trạm qua MQTT Payload.

---

## 🔁 SELF REVIEW LOOP (Phase 16)

> [!NOTE]
> **Vai trò: Principal UX Researcher**
> - *Điểm mạnh:* Việc tận dụng PIR Sensor để chuyển đổi State màn hình (từ Quảng cáo sang Chế độ nghe) tạo cảm giác cực kỳ "Smart" và tiết kiệm thao tác (Zero-touch) cho người khiếm thị.
> - *Rủi ro:* Cảm biến PIR có thể nhận diện nhầm con chó/mèo hoặc túi nilon bay qua là người, khiến màn hình nhảy loạn xạ.
> - *Cải tiến:* Thêm logic Debounce ở cấp độ C++: Chỉ chuyển State khi phát hiện mục tiêu liên tục trong >= 1.5 giây. Nếu chỉ nhá lên rồi tắt (con vật chạy qua) thì bỏ qua. Đã thêm vào thiết kế Software (Phase 9).

> **Trạng thái Phase 16:** ✅ Đã thông qua Quality Gate.
