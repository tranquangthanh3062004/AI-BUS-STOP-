# RISKS: Phân tích Rủi ro và Khó khăn (Phần 10)

## 1. Mục tiêu (Objective)
Nhận diện sớm các nguy cơ có thể khiến dự án thất bại hoặc đội chi phí, từ đó chuẩn bị phương án dự phòng (Mitigation Plan).

## 2. Phạm vi (Scope)
Bao gồm rủi ro về Công nghệ AI, Phần cứng vật lý, Pháp lý, và Vận hành.

## 3. Dàn ý chi tiết

### 3.1. Rủi ro Công nghệ (Hallucination)
- **Vấn đề:** Local LLM bị "ảo giác" (Hallucination), chỉ đường sai hoặc cung cấp thông tin vé sai.
- **Giải pháp:** Sử dụng Strict Local RAG. Ép LLM luôn bắt đầu bằng câu "Theo dữ liệu của Sở GTVT...", nếu không tìm thấy trong RAG, LLM bắt buộc trả lời "Tôi không rõ thông tin này".

### 3.2. Rủi ro Phần cứng & Vận hành
- **Vấn đề:** Bị mất trộm linh kiện hoặc phá hoại màn hình.
- **Giải pháp:** Sử dụng ốc vít chống trộm đặc chủng. Kính cường lực IK10 (Chống búa đập). Màn hình E-ink có nắp mica bảo vệ.

### 3.3. Rủi ro Năng lượng
- **Vấn đề:** Nếu dùng năng lượng mặt trời, Kiosk có thể tắt nguồn vào những ngày mưa bão kéo dài.
- **Giải pháp:** Kiosk tự động hạ xung nhịp CPU, tắt LLM và chỉ hiển thị bản đồ tĩnh E-ink (tiêu thụ 0W) khi pin < 20%.

## 4. Các nội dung sẽ phát triển tiếp theo
- Lập ma trận Rủi ro (Risk Matrix: Impact x Probability) cho từng giai đoạn dự án.
