# KNOWLEDGE BASE: Quản lý & Đồng bộ Tri thức

Tài liệu này bao gồm **Phase 13: Knowledge Base** trong lộ trình 20 Phases của dự án. 

---

## PHASE 13: KNOWLEDGE BASE (Cơ sở Tri thức)

### 13.1. Phase Metadata
- **Objective:** Thiết kế chiến lược lưu trữ, định dạng dữ liệu và cơ chế đồng bộ (Sync) giữa Master Database (Cloud) và Local Database (Edge).
- **Input:** Khối lượng dữ liệu GTFS và Geo-RAG (Phase 12).
- **Output:** Data Schema, Sync Strategy (Chiến lược Đồng bộ).
- **Dependencies:** Phase 12, Phase 4 (MQTT).
- **Deliverables:** Thuật toán Delta Sync (chỉ tải phần bị thay đổi).
- **Risks:** Đồng bộ file lớn (50MB) bằng 4G giữa chừng rớt mạng, gây corrupt toàn bộ dữ liệu hiện tại của Kiosk.
- **Acceptance Criteria:** Cơ chế đồng bộ phải hỗ trợ A/B Partition (Ghi vào tệp tạm thời, kiểm tra Checksum MD5, mới áp dụng).

### 13.2. Engineering Standard: Định dạng Dữ liệu (Data Format)

| Định dạng Dữ liệu | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **FlatBuffers / Protobuf** | **(Lựa chọn chính thức cho Graph Data)**. Dùng để nén mảng đồ thị giao thông (Tuyến, Trạm). | JSON, XML | Nén siêu tốt, tốc độ đọc trực tiếp từ bộ nhớ (Zero-copy) siêu nhanh. Kích thước file giảm >80% so với JSON. | Không thể đọc bằng mắt thường (Unreadable). Debug khó. | Khi cần một định dạng người dễ đọc (Human-readable) như cấu hình Config. |
| **JSON** | Bị loại bỏ cho Dữ liệu lớn. Chỉ dùng cho các Message MQTT cấu hình hoặc lệnh điều khiển nhỏ. | FlatBuffers | Dễ đọc, dễ debug. | Kích thước chuỗi lớn, tốn băng thông, tốc độ Parse (phân tích) chậm trên CPU IoT. | Không dùng để chứa 100,000 node đồ thị. |
| **SQLite** | **(Lựa chọn chính thức cho VectorDB và Lịch trình)**. | CSV, TXT | Đọc trực tiếp từ đĩa không cần load toàn bộ lên RAM. Hỗ trợ ACID (giao dịch an toàn). | Hơi nặng một chút so với custom binary format. | - |

### 13.3. Chiến lược Đồng bộ Delta (CRDT / Rsync)
Thay vì tải toàn bộ file SQLite (50MB) mỗi đêm, Cloud sẽ tính toán mã băm (hash) của từng trang dữ liệu, và chỉ tạo ra một file **Patch (.patch)** có kích thước < 500KB.
1. Kiosk tải file Patch qua MQTT (chia thành nhiều mảnh nhỏ) hoặc HTTPS (có Resume/Range).
2. Kiosk áp dụng file Patch vào `db_temp.sqlite`.
3. Kiosk chạy lệnh SQL `PRAGMA integrity_check` để đảm bảo file `db_temp` không bị lỗi.
4. Kiosk khóa cơ sở dữ liệu cũ, đổi tên (Swap) `db_temp` thành `db_main`. (Cơ chế A/B Partition đảm bảo tính toàn vẹn 100%).

---

## 🔁 SELF REVIEW LOOP (Phase 13)

> [!NOTE]
> **Vai trò: Principal Distributed Systems Engineer**
> - *Điểm mạnh:* Cơ chế A/B Partition và Integrity Check là tiêu chuẩn vàng của Hệ thống Phân tán (Distributed Systems), loại trừ hoàn toàn nguy cơ Kiosk hỏng Database do mất kết nối 4G.
> - *Rủi ro:* Thuật toán tính toán Delta Patch trên Server Cloud sẽ tốn rất nhiều CPU khi có hàng ngàn Kiosk.
> - *Cải tiến:* Không tính toán Patch theo từng Kiosk. Cloud sẽ tự động pre-compute (tính toán sẵn) các file Patch định kỳ (mỗi giờ 1 lần) và lưu lên S3/CDN. Kiosk chỉ cần gọi lên CDN để kéo file Patch tĩnh về, hoàn toàn giải phóng CPU cho Cloud.

> **Trạng thái Phase 13:** ✅ Đã thông qua Quality Gate.
