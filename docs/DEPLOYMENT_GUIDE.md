# DEPLOYMENT GUIDE: Triển khai & Cập nhật OTA

Tài liệu này bao gồm **Phase 19: Deployment** trong lộ trình 20 Phases của dự án. 

---

## PHASE 19: DEPLOYMENT (Chiến lược Triển khai)

### 19.1. Phase Metadata
- **Objective:** Xác định quy trình từ lúc thiết bị xuất xưởng (Factory) đến lúc lắp đặt ngoài vỉa hè (Field) và cách cập nhật phần mềm từ xa (OTA) cho hàng nghìn Kiosk cùng lúc.
- **Input:** Cấu trúc Software (Phase 9) và Security (Phase 18).
- **Output:** Provisioning Flow, OTA Strategy.
- **Dependencies:** Phase 9, 18.
- **Deliverables:** Hướng dẫn cấu hình Zero-Touch Provisioning.
- **Risks:** Cập nhật OTA phần mềm AI bị lỗi giữa chừng khiến Kiosk hiển thị màn hình đen ngoài đường, phải cử người đi cắm cáp sửa.
- **Acceptance Criteria:** Kiosk phải tự động khôi phục bản phần mềm cũ (Rollback) trong vòng 3 phút nếu bản cập nhật mới OTA thất bại.

### 19.2. Engineering Standard: Chiến lược Cập nhật (OTA Strategy)

| Giải pháp OTA | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **Mender.io (A/B Rootfs)** | **(Lựa chọn chính thức)**. Tiêu chuẩn công nghiệp cho thiết bị nhúng. | Balena / Ansible | Thay vì cập nhật từng file, Mender cập nhật Cả hệ điều hành (Image-based). Nếu Image mới không Boot lên được, mạch sẽ tự động nhảy về Image phân vùng B (cũ) hoàn toàn không để lại dấu vết lỗi. | File cập nhật Image khá lớn (Vài trăm MB đến GB). | Khi chỉ cần cập nhật một script Python nhỏ vài KB (lúc đó dùng Docker Pull). |
| **Docker Compose Pull** | Bị loại bỏ cho OS. Chỉ dùng để cập nhật App. | K3s (Kubernetes) | Cập nhật App rất nhanh. | Nếu bản cập nhật làm treo tiến trình Docker Daemon, thiết bị sẽ Brick (tê liệt vĩnh viễn). | Quản lý thiết bị từ xa cấp hệ thống (System-level). |

### 19.3. Quy trình Zero-Touch Provisioning (ZTP)
1. Kiosk lắp ráp tại xưởng chỉ chứa Hệ điều hành gốc, KHÔNG chứa Model AI.
2. Nhân viên bê Kiosk ra vỉa hè, cấp nguồn, cắm SIM 4G. Bật công tắc điện.
3. Kiosk lấy địa chỉ MAC và Chip ID gọi lên Cloud. Cloud xác thực đây là phần cứng hợp lệ.
4. Cloud đẩy chứng chỉ mTLS và Key mã hóa LUKS (Phase 18) xuống Kiosk.
5. Kiosk tự động tải Model `llama-3-8b.gguf` và VectorDB 5km tương ứng với tọa độ GPS của trạm đó. Tự động khởi động và sẵn sàng phục vụ. (Nhân viên lắp đặt không cần gõ bất cứ dòng lệnh nào).

---

## 🔁 SELF REVIEW LOOP (Phase 19)

> [!NOTE]
> **Vai trò: Principal SRE (Site Reliability Engineer)**
> - *Điểm mạnh:* Zero-Touch Provisioning giảm tối đa chi phí nhân công lắp đặt (Chỉ cần mướn thợ điện nước, không cần kỹ sư IT ra hiện trường).
> - *Rủi ro:* Tải Model AI 5.5GB qua SIM 4G lúc lắp đặt sẽ rất lâu và tốn tiền gói cước Data.
> - *Cải tiến:* Yêu cầu nhân viên lắp đặt mang theo một USB cài đặt đặc biệt (Provisioning USB). Kiosk sẽ ưu tiên quét USB để lấy file `llama.3-8b.gguf` trước. Chỉ những file siêu nhỏ như VectorDB (50MB) mới tải qua 4G. Điều này giải quyết hoàn hảo bài toán chi phí mạng. Đã đưa vào thiết kế.

> **Trạng thái Phase 19:** ✅ Đã thông qua Quality Gate. Sẵn sàng chuyển sang Phase cuối cùng.
