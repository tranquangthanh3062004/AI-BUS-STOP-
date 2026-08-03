# PROJECT OVERVIEW: Offline AI Smart Bus Stop Assistant

Tài liệu này bao gồm **Phase 1: Research** và **Phase 3: Business Analysis** trong lộ trình 20 Phases của dự án. 

---

## PHASE 1: RESEARCH (Nghiên cứu Thực trạng & Giải pháp)

### 1.1. Phase Metadata
- **Objective:** Đánh giá thực trạng các giải pháp Kiosk xe buýt hiện tại trên thế giới và xác định ranh giới công nghệ cho Edge AI.
- **Input:** Báo cáo thị trường Smart City, hạn chế của hệ thống Kiosk truyền thống.
- **Output:** Danh sách các giới hạn cần phá vỡ và hướng tiếp cận công nghệ.
- **Dependencies:** Không có.
- **Deliverables:** Tài liệu phân tích thực trạng.
- **Risks:** Đánh giá sai năng lực của thiết bị Edge dẫn đến kỳ vọng quá cao (Hallucination về phần cứng).
- **Acceptance Criteria:** Tài liệu chỉ ra được ít nhất 3 hạn chế cốt lõi của hệ thống hiện tại và đề xuất 1 hướng đi mới khả thi về mặt khoa học.

### 1.2. Engineering Standard: Lựa chọn Hướng tiếp cận
**Bài toán:** Trạm xe buýt thường bị mất kết nối Internet hoặc có băng thông rất hẹp vào giờ cao điểm. Các Kiosk hiện tại (như Citymapper Smart Panel, Moovit Kiosk) chỉ hoạt động được khi có mạng, nếu rớt mạng sẽ trở thành "cục gạch" hoặc chỉ hiển thị ảnh tĩnh.

| Hướng tiếp cận | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào nên dùng |
|---|---|---|---|---|---|
| **Cloud-Only AI (Hiện tại)** | Không chọn vì phụ thuộc hoàn toàn vào Internet, độ trễ cao khi mạng chậm. | **Hybrid Edge-Cloud (Được chọn)** | Dễ lập trình, không tốn tài nguyên thiết bị vật lý. | Chết toàn bộ hệ thống khi đứt cáp quang hoặc nghẽn mạng 4G. | Các trạm thông tin trong nhà ga Metro (có wifi/LAN ổn định). |
| **Hybrid Edge-Cloud AI (Đề xuất)** | Hoạt động độc lập (Resilience). AI chạy cục bộ, chỉ dùng Cloud để lấy dữ liệu realtime (GPS) siêu nhẹ. | Fully Offline AI | Đảm bảo tính sẵn sàng 99.9%. Trải nghiệm mượt mà không độ trễ do gọi LLM trực tiếp trên máy. | Chi phí phần cứng cao hơn (cần NPU/GPU). Cần cơ chế đồng bộ phức tạp. | Bắt buộc đối với môi trường ngoài trời (Outdoor Kiosk), mạng di động không ổn định. |

---

## PHASE 3: BUSINESS ANALYSIS (Phân tích Kinh doanh & Nhu cầu)

### 3.1. Phase Metadata
- **Objective:** Xác định User Persona, Pain Points, và giá trị mang lại cho Stakeholders để định hình sản phẩm.
- **Input:** Kết quả Research từ Phase 1.
- **Output:** Hồ sơ người dùng, Ma trận giá trị.
- **Dependencies:** Phase 1 & 2.
- **Deliverables:** Dữ liệu phân tích hành vi hành khách.
- **Risks:** Không phù hợp với ngân sách của chính quyền thành phố (B2G).
- **Acceptance Criteria:** Xác định được ít nhất 3 đối tượng người dùng chính và giá trị khoa học/kinh tế cụ thể.

### 3.2. User Persona & Pain Points
1. **Người cao tuổi / Người khiếm thị:** 
   - *Pain Point:* Chữ trên bảng LED quá nhỏ hoặc không thể nhìn thấy. Không biết thao tác màn hình cảm ứng phức tạp.
   - *Kỳ vọng:* Tương tác bằng giọng nói tiếng Việt tự nhiên, hỏi và nhận câu trả lời ngay lập tức.
2. **Khách du lịch quốc tế:** 
   - *Pain Point:* Rào cản ngôn ngữ, không có SIM 4G để dùng Google Maps, không biết cách mua vé.
   - *Kỳ vọng:* Kiosk tự động nhận diện tiếng Anh và hướng dẫn lộ trình.
3. **Cơ quan Quản lý (Sở GTVT):** 
   - *Pain Point:* Thiếu dữ liệu phân tích luồng hành khách tại điểm dừng.
   - *Kỳ vọng:* Kiosk đóng vai trò như một Node IoT thu thập dữ liệu đám đông (ẩn danh).

### 3.3. Business Value & Scientific Value
- **Business Value (B2G/B2B):** Tăng 20% lượng người dùng giao thông công cộng nhờ việc dễ tiếp cận thông tin. Giảm chi phí CSKH tại các trạm điều hành. Tích hợp Ad-Tech (quảng cáo số) mang lại dòng tiền.
- **Scientific Value:** Đóng góp nghiên cứu về "Decentralized RAG on Low-Power Devices" (RAG phi tập trung trên thiết bị tiêu thụ điện thấp) và "Zero-Latency Voice AI" trong môi trường ồn ào.

---

## 🔁 SELF REVIEW LOOP (Phase 1 & 3)

> [!NOTE]
> **Vai trò: Principal UX Researcher**
> - *Điểm mạnh:* Nhắm đúng vào nhóm người dùng yếu thế (Accessibility-first) vốn bị bỏ quên bởi các app di động.
> - *Rủi ro:* Tương tác giọng nói ngoài đường phố rất ồn ào, tỷ lệ nhận diện (STT) có thể rớt thảm hại.
> - *Cải tiến:* Chuyển sang Phase tiếp theo phải nhấn mạnh yêu cầu phần cứng: Microphone Array có chống ồn DSP phần cứng. Đã cập nhật định hướng.

> [!NOTE]
> **Vai trò: Principal Product Manager**
> - *Điểm mạnh:* Đưa Ad-Tech vào làm Business Value giúp thuyết phục nhà đầu tư B2B.
> - *Rủi ro:* Cần cẩn thận cân bằng giữa quảng cáo và thông tin xe buýt, tránh làm người dùng khó chịu.
> - *Cải tiến:* Quy định: Khi Kiosk phát hiện có người tới gần (PIR Sensor), quảng cáo phải tự động biến mất để hiển thị bản đồ xe buýt.

> **Trạng thái Phase 1 & 3:** ✅ Đã thông qua Quality Gate.
