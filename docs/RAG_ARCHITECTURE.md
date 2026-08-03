# RAG ARCHITECTURE: Tăng cường Kiến thức Cục bộ (Local RAG)

Tài liệu này bao gồm **Phase 12: RAG Architecture** trong lộ trình 20 Phases của dự án. 

---

## PHASE 12: RAG ARCHITECTURE (Kiến trúc RAG Cục bộ)

### 12.1. Phase Metadata
- **Objective:** Đưa hệ thống RAG (Retrieval-Augmented Generation) từ môi trường Cloud với tài nguyên dồi dào xuống thiết bị Edge bị giới hạn RAM, giúp LLM có dữ liệu chính xác về Luật giao thông và Giá vé.
- **Input:** Khả năng LLM (Phase 11).
- **Output:** Quy trình Chunking, Embedding, và Retrieval siêu tinh gọn.
- **Dependencies:** Phase 11.
- **Deliverables:** Mô hình Local VectorDB, Local Embedding Model.
- **Risks:** Lựa chọn mô hình Embedding quá nặng (ví dụ: > 1GB) sẽ lấn chiếm bộ nhớ VRAM của LLM, gây ra lỗi Out of Memory (OOM).
- **Acceptance Criteria:** Tốc độ tìm kiếm (Retrieval latency) Top-K (K=3) trên bộ nhớ Edge phải < 100ms. Kích thước mô hình Embedding < 200MB.

### 12.2. Engineering Standard: Lựa chọn Mô hình Embedding

| Mô hình Embedding | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **Multilingual-E5-small** | **(Lựa chọn chính thức)**. Dung lượng chỉ khoảng 130MB. Hỗ trợ Tiếng Việt xuất sắc. Dễ dàng chạy qua ONNX Runtime trên CPU mà không cần GPU. | bge-m3 | Trọng lượng lông hồng (Lightweight), embed tốc độ ánh sáng (<20ms). Giữ nguyên không gian VRAM quý giá cho LLM. | Chiều vector (Dimension) chỉ là 384, độ chính xác ngữ nghĩa có thể thua các mô hình lớn. | Khi cần so sánh ngữ nghĩa của các đoạn văn bản học thuật siêu phức tạp. |
| **bge-m3** | Bị loại bỏ. Dung lượng > 2GB (cực kỳ lãng phí RAM). | Nomic-Embed | Retrieval cực kỳ chính xác đa ngôn ngữ. | Quá nặng cho thiết bị Edge (Jetson Nano 8GB đã bị Llama-3 chiếm mất 5.5GB). | Trên Edge Devices có RAM <= 8GB. |

### 12.3. Quy trình Local RAG (Offline Retrieval)
Thay vì nhúng (Embed) và tạo Vector Database trực tiếp trên Kiosk, quy trình được **phân mảnh (Decoupled)** như sau:
1. **Cloud Indexing:** Đám mây (Backend) tải các file PDF (Luật, Giá vé), cắt Chunk, chạy qua E5-small để tạo VectorDB bằng ChromaDB. Toàn bộ file SQLite của ChromaDB được đẩy xuống Kiosk.
2. **Edge Retrieval:** Khi user hỏi, Kiosk chỉ thực hiện thao tác Đọc (Read-only Search) trên file SQLite đó. Kiosk cũng chạy E5-small (ONNX) để nhúng câu hỏi của user thành vector, rồi so sánh Cosine Similarity.
3. **Bán kính Địa lý (Geo-Fencing RAG):** VectorDB đẩy xuống mỗi Kiosk là KHÁC NHAU. Kiosk tại Bến Thành chỉ nhận file VectorDB chứa các địa danh, tuyến xe buýt trong bán kính 5km quanh Bến Thành. Đây là kỹ thuật *Decentralized Geo-RAG* đột phá, giảm kích thước CSDL từ 10GB xuống còn 50MB.

---

## 🔁 SELF REVIEW LOOP (Phase 12)

> [!NOTE]
> **Vai trò: Principal RAG Engineer**
> - *Điểm mạnh:* Kỹ thuật "Geo-Fencing RAG" (chỉ tải dữ liệu trong bán kính 5km) là một nước đi xuất sắc (Masterstroke) để giải quyết bài toán Memory Constraint (giới hạn bộ nhớ) trên Edge Device.
> - *Rủi ro:* Câu hỏi của hành khách có thể vượt ngoài bán kính 5km (Ví dụ đứng ở Bến Thành nhưng hỏi đường đi Suối Tiên cách 20km). RAG cục bộ sẽ thất bại.
> - *Cải tiến:* Thêm luật cho Local LLM: Cấu trúc Graph nội bộ chứa tất cả Node chính của thành phố, nhưng VectorDB (điểm du lịch, quán ăn) thì bị giới hạn 5km. Do đó, tìm đường vẫn được, nhưng hỏi địa danh xa thì Kiosk sẽ từ chối hoặc yêu cầu mạng. Thiết kế này đã được chấp nhận.

> **Trạng thái Phase 12:** ✅ Đã thông qua Quality Gate.
