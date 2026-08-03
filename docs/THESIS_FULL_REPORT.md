# BÁO CÁO ĐỒ ÁN: TÍCH HỢP HỆ THỐNG TRỢ LÝ AI TRẠM XE BUÝT THÔNG MINH HOẠT ĐỘNG NGOẠI TUYẾN TRÊN THIẾT BỊ BIÊN (EDGE AI)

## CHƯƠNG 1: MỞ ĐẦU

### 1.1. Tính cấp thiết của đề tài
Sự phát triển của Đô thị Thông minh (Smart City) và Hệ thống Giao thông Thông minh (ITS - Intelligent Transportation Systems) đặt ra yêu cầu cấp thiết về việc nâng cao chất lượng dịch vụ vận tải hành khách công cộng. Trạm xe buýt không chỉ là nơi dừng đón trả khách đơn thuần, mà đang từng bước biến đổi thành các Smart Bus Stop Kiosk – điểm tương tác đa phương tiện cung cấp thông tin lộ trình, thời gian chạy xe, giá vé và hướng dẫn di chuyển cho hành khách.

Tuy nhiên, hạ tầng mạng di động (4G/5G) tại các trạm xe buýt ngoài trời thường gặp rủi ro đứt kết nối, chập chờn hoặc nghẽn mạng vào giờ cao điểm. Hầu hết các giải pháp Kiosk truyền thống dựa hoàn toàn vào Cloud API (Cloud-only) sẽ ngừng hoạt động khi rớt mạng, gây gián đoạn thông tin và ảnh hưởng nghiêm trọng đến trải nghiệm hành khách. Từ thực tiễn đó, việc nghiên cứu một trợ lý AI có khả năng tương tác tự nhiên, hoạt động độc lập không cần Internet (Offline Mode) tại trạm xe buýt là một nhu cầu cấp thiết và mang tính thực tiễn cao.

### 1.2. Mục tiêu nghiên cứu
**Mục tiêu tổng quát:** 
Nghiên cứu và phát triển hệ thống "AI Smart Bus Stop Assistant" – Trợ lý AI tương tác giọng nói và bản đồ thông minh cho trạm xe buýt, có khả năng hoạt động 100% ngoại tuyến dựa trên kiến trúc Điện toán Biên (Edge AI), kết hợp mô hình Ngôn ngữ Lớn Cục bộ (Local LLM), Kỹ thuật Truy xuất Tăng cường (Local RAG) và Cơ chế Chống Ảo giác (Anti-Hallucination Validator).

**Mục tiêu cụ thể:**
- Thiết kế và cài đặt kiến trúc Hybrid Edge-Cloud AI có khả năng tự động phát hiện và chuyển đổi mượt mà giữa chế độ Online và Offline.
- Xây dựng Edge AI Pipeline 5 bước tối ưu cho thiết bị phần cứng nhúng: Chuẩn hóa -> Phân loại Ý định -> Truy xuất Cục bộ -> Sinh ngôn ngữ LLM -> Chống Ảo giác.
- Xây dựng Chiến lược Phản hồi 3 tầng (3-Tier Fallback Strategy) để đảm bảo độ tin cậy và không bao giờ bị gián đoạn hoạt động, kể cả trên phần cứng không có NPU/GPU.
- Phát triển giao diện Kiosk UI hiện đại tích hợp bản đồ tương tác Leaflet và công nghệ giọng nói (STT/TTS) thân thiện với người dùng.

### 1.3. Đối tượng và Phạm vi nghiên cứu
**Đối tượng:** 
- Mô hình Ngôn ngữ Lớn (LLM) thu gọn chạy trên thiết bị cục bộ (Qwen2.5:3B, Llama-3-8B).
- Các thuật toán tìm kiếm lộ trình và xử lý ngôn ngữ tự nhiên Tiếng Việt (Intent Classification, Entity Recognition).
- Kỹ thuật RAG (Retrieval-Augmented Generation) cục bộ.

**Phạm vi:** 
- **Dữ liệu thực nghiệm:** Toàn bộ mạng lưới xe buýt Hà Nội (136 tuyến, 590 trạm), xe buýt TP.HCM, tuyến Metro 2A Cát Linh - Hà Đông, Metro 3 Nhổn - Ga Hà Nội, Metro 1 Bến Thành - Suối Tiên, và các quy định hành lý/vé tháng giao thông công cộng.
- **Môi trường thử nghiệm:** Chạy thực tế trên hạ tầng FastAPI (Backend) và Chrome Kiosk Interface (Frontend) trên các thiết bị Edge PC hoặc máy tính nhúng (ARM64 - Jetson / AMD64).

### 1.4. Nội dung thực hiện
- Thu thập, làm sạch và số hóa dữ liệu mạng lưới tuyến xe buýt và các quy định giao thông.
- Thiết kế cơ sở dữ liệu SQLite tối ưu để lưu trữ dữ liệu dạng đồ thị tuyến điểm.
- Phát triển module phân loại ý định (Intent Classifier) và trích xuất thực thể.
- Xây dựng Local RAG để truy vấn dữ liệu có cấu trúc và phi cấu trúc ngoại tuyến.
- Tích hợp và tối ưu mô hình Ollama, llama.cpp.
- Phát triển lớp Validator chống ảo giác để bảo đảm độ chính xác 100%.
- Xây dựng giao diện Web Kiosk tương tác đa phương tiện (Bản đồ, Giọng nói).
- Kiểm thử và đánh giá hiệu năng, độ trễ của hệ thống.

### 1.5. Phương pháp thực hiện
- **Phương pháp nghiên cứu lý thuyết:** Tổng hợp các tài liệu về Edge AI, LLM, RAG và tối ưu hóa mô hình AI trên thiết bị hạn chế tài nguyên.
- **Phương pháp thu thập và phân tích dữ liệu:** Tổng hợp dữ liệu GTCC từ các nguồn chính thống, tiền xử lý và cấu trúc hóa dữ liệu.
- **Phương pháp thực nghiệm và phát triển phần mềm (SDLC):** Ứng dụng mô hình Agile, chia nhỏ các giai đoạn phát triển thành các component độc lập (Backend, Frontend, Edge AI, Speech).
- **Phương pháp kiểm thử (Testing):** Sử dụng Pytest để xây dựng các kịch bản kiểm thử tự động (Unit Test, End-to-End Test) đánh giá tính chính xác và đo lường độ trễ (Latency).

---

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG

### 2.1. Cơ sở lý thuyết
- **Điện toán Biên (Edge AI):** Cho phép thực thi các thuật toán AI trực tiếp trên thiết bị phần cứng tại biên (như Kiosk), giảm thiểu sự phụ thuộc vào Cloud, bảo mật dữ liệu và loại bỏ độ trễ do đường truyền mạng.
- **Mô hình Ngôn ngữ Lớn Cục bộ (Local LLM):** Ứng dụng các phiên bản mô hình ngôn ngữ đã được nén (Quantization - GGUF) như Qwen2.5 hoặc Llama 3 để có thể suy luận trực tiếp trên CPU/GPU thiết bị biên mà vẫn duy trì được khả năng hiểu ngôn ngữ tự nhiên.
- **Retrieval-Augmented Generation (RAG):** Kỹ thuật kết hợp giữa năng lực sinh văn bản của LLM và khả năng truy vấn dữ liệu từ cơ sở tri thức cục bộ. Giúp cung cấp cho LLM bối cảnh chính xác để trả lời các câu hỏi đặc thù (lộ trình, giá vé) mà không phải học thuộc trong quá trình huấn luyện.
- **Hallucination Mitigation (Giảm thiểu Ảo giác):** Cơ chế kiểm duyệt đầu ra của AI nhằm đảm bảo LLM không tạo ra các thông tin sai lệch, không tồn tại trong tập dữ liệu gốc, đặc biệt quan trọng đối với dữ liệu giao thông thực tế.

### 2.2. Công nghệ sử dụng
- **Backend Server:** Python 3.11, FastAPI, Uvicorn (Framework bất đồng bộ hiệu năng cao, hỗ trợ Pydantic Validation và OpenAPI).
- **Edge Database:** SQLite 3 (Truy vấn đồ thị quan hệ), JSON Store (Lưu trữ tri thức FAQ phi cấu trúc).
- **Local LLM Engine:** Ollama, llama.cpp (Trình quản lý và suy luận LLM tối ưu hóa cho phần cứng cục bộ).
- **Frontend Kiosk UI:** HTML5, CSS3 Vanilla, JavaScript ES6 (Đảm bảo độ nhẹ, phản hồi mượt mà không phụ thuộc framework nặng nề).
- **Bản đồ Tương tác:** Leaflet.js kết hợp OpenStreetMap.
- **Xử lý Giọng nói:** Web Speech API kết hợp module C++ thấp tầng (Whisper.cpp cho STT và Piper cho TTS).
- **Môi trường & Đóng gói:** Docker, Docker Compose đa nền tảng (ARM64/AMD64).

### 2.3. Các nghiên cứu liên quan
Các giải pháp tìm kiếm giao thông công cộng hiện hành phổ biến như Google Maps, BusMap hay Citymapper được thiết kế chủ yếu cho thiết bị di động cá nhân. Chúng tồn tại nhiều điểm nghẽn khi đưa lên không gian công cộng:
- Phụ thuộc vào kết nối 4G/5G liên tục để gọi API.
- Gọi LLM Đám mây (OpenAI GPT, Gemini) tốn kém chi phí, phát sinh độ trễ từ 1.5 - 4s, không đạt chuẩn thời gian thực cho tương tác giọng nói.
- Rào cản người dùng: Người già, trẻ em hay du khách nước ngoài không có 4G sẽ gặp khó khăn.

### 2.4. Giải pháp đề xuất
Đề xuất giải pháp **Hybrid Edge-Cloud AI Architecture**, trong đó Edge Device (Kiosk) đóng vai trò trung tâm xử lý dữ liệu và AI cục bộ khi không có mạng (Offline Mode) với chiến lược 3 tầng an toàn. Khi có mạng (Online Mode), hệ thống đồng bộ dữ liệu tĩnh và cập nhật vị trí xe theo thời gian thực (GTFS-RT). Giải pháp này xóa bỏ rủi ro rớt mạng, tiết kiệm hoàn toàn chi phí API AI đám mây.

---

## CHƯƠNG 3: PHÂN TÍCH, THIẾT KẾ VÀ XÂY DỰNG HỆ THỐNG

### 3.1. Phân tích yêu cầu
- **Yêu cầu chức năng:**
  - Nhận diện giọng nói hoặc văn bản tiếng Việt của hành khách.
  - Phân loại 6 nhóm ý định (Intent): Tra cứu lộ trình, giá vé, giờ chạy, quy định, thông tin Metro, và các câu hỏi rác (Unknown).
  - Tìm kiếm lộ trình tối ưu (đi thẳng hoặc chuyển 1 tuyến) trên bản đồ.
  - Trả lời thông tin trích xuất bằng giọng nói (TTS) và hiển thị thẻ thông tin trực quan.
- **Yêu cầu phi chức năng:**
  - Hệ thống phải hoạt động offline 100%.
  - Độ trễ trả về (Latency) phải nhỏ hơn 3s đối với LLM và dưới 100ms đối với Fast Pipeline.
  - Tỉ lệ chính xác thông tin 100% (Zero Hallucination).

### 3.2. Thiết kế hệ thống tổng thể (System Pipeline)
Kiến trúc bao gồm các module chính liên kết chặt chẽ:
1. **Kiosk UI:** Thu thập truy vấn (STT/Text) -> Hiển thị kết quả, bản đồ, đọc TTS.
2. **FastAPI Core Service:** Middleware nhận request, làm sạch dữ liệu (Sanitize) và kiểm tra trạng thái mạng.
3. **Edge AI Engine (5 bước):**
   - *Query Normalizer:* Chuẩn hóa văn bản ("bx mỹ đình" -> "bến xe mỹ đình").
   - *Intent Classifier:* Dùng thuật toán Regex nhận diện ý định.
   - *Local Retriever (RAG):* Kết nối với CSDL SQLite để tìm lộ trình, hoặc JSON Store tìm FAQ.
   - *Local LLM Engine:* Tổng hợp sinh câu trả lời bằng Qwen2.5:3B hoặc Local Summarizer.
   - *Output Validator:* Kiểm duyệt câu trả lời, loại bỏ ảo giác.

### 3.3. Thiết kế cơ sở dữ liệu
CSDL `local_transit.db` được thiết kế chuẩn hóa trên SQLite:
- `routes`: (route_id, route_name, start_stop, end_stop, operating_hours, frequency, fare_vnd, itinerary, city).
- `stops`: (stop_id, stop_name, district, city).
- `route_stops`: (route_id, stop_name, stop_sequence, direction) - Liên kết N-N để phục vụ thuật toán định tuyến.
- Cơ sở tri thức phi cấu trúc `faq_store.json` chứa các văn bản về nội quy, luật GTCC.

### 3.4. Thiết kế giao diện
Giao diện (Kiosk UI) thiết kế theo hướng Dark Theme, High-Contrast & Voice-first:
- **Khu vực Trái:** Thanh tương tác giọng nói với hiệu ứng sóng âm (Wave Animation) và nút bấm nhanh.
- **Khu vực Giữa:** Cửa sổ chat hiển thị hội thoại, các thẻ (Cards) thông tin tuyến buýt, giá vé, giờ chạy.
- **Khu vực Phải:** Bản đồ Leaflet.js tương tác, tự động vẽ đường (Polyline) nối các trạm đi/đến.

### 3.5. Xây dựng hệ thống
- **Xây dựng Local RAG (Hybrid Retrieval):** Xử lý luồng truy vấn cấu trúc thông qua thuật toán đếm số lần chuyển tuyến và luồng truy vấn ngữ nghĩa cho FAQ.
- **Chiến lược LLM 3 tầng (3-Tier Fallback):**
  - Tầng 1: Sử dụng Ollama (Qwen2.5:3B) để sinh ngôn ngữ tự nhiên.
  - Tầng 2: Dùng trực tiếp llama.cpp GGUF nếu Ollama gặp lỗi.
  - Tầng 3: Local Deterministic Summarizer (Mẫu code cứng) nếu không có tài nguyên chạy AI để đạt độ trễ < 2ms, hệ thống không bao giờ crash.
- **Xây dựng Validator chống ảo giác:** Trích xuất tập $V_{valid}$ (các tuyến có thật) từ RAG. So sánh với $A_{raw}$ do LLM sinh ra. Nếu LLM nhắc đến tuyến xe ngoài $V_{valid}$, hủy văn bản và trả về Fallback an toàn mặc định.

---

## CHƯƠNG 4: KẾT QUẢ VÀ THẢO LUẬN

### 4.1. Kết quả thực nghiệm
Hệ thống đã triển khai thành công 100% dữ liệu ngoại tuyến bao gồm:
- 136 tuyến xe buýt và 590 điểm dừng tại Hà Nội/TP.HCM.
- Dữ liệu các tuyến Metro trọng điểm.
Hệ thống xử lý xuất sắc các kịch bản tra cứu từ tuyến đi thẳng, tuyến chuyển 1 lần, giá vé, cho đến nội quy. Tích hợp trơn tru với bản đồ Leaflet để vẽ lộ trình thực tế.

### 4.2. Đánh giá hệ thống (Cập nhật Thực tế)
**1. Đánh giá dựa trên Pytest (Automated Test Suite):**
Tiến hành chạy lại toàn bộ 16 Test Cases tự động (`pytest tests/`) trên mã nguồn thực tế mới nhất, kết quả đạt **15/16 Pass (93.75%)** và **1 Failed (6.25%)**:
- **Các kịch bản Core Edge AI (Pass):** 100% các kịch bản tra cứu tuyến đường (Mỹ Đình -> Bách Khoa trả về Tuyến 26), kiểm thử độ trễ, tra giá vé, và kịch bản Anti-Hallucination (Hỏi Tuyến 999 trả về Fallback an toàn) đều vượt qua thành công với độ trễ siêu thấp (Fast mode ~ 15-45ms). Tính năng loại bỏ XSS/Script Injection hoạt động tốt.
- **Kịch bản UI (Failed):** Kịch bản `test_static_ui_page` thất bại do giao diện Kiosk UI (`index.html`) đã được nâng cấp thiết kế (đổi Title thành *"Trạm Xe Buýt Thông Minh - Kiosk Tra Cứu"*), nhưng mã nguồn Unit Test chưa được cập nhật theo kịch bản mới (chứa Assert cũ *"AI Smart Bus Stop"*).
*=> Kết luận:* Core AI Pipeline hoạt động cực kỳ ổn định và chính xác. Sự sai lệch kết quả kiểm thử chỉ xuất phát từ việc thiếu đồng bộ mã Unit Test với thiết kế giao diện UI mới.

**2. Đánh giá RAG và LLM (DeepEval Framework):**
Hệ thống có bao gồm thư mục lưu trữ môi trường đánh giá `.deepeval`, hướng đến việc sử dụng DeepEval để đánh giá chuyên sâu các chuẩn mực của RAG (Faithfulness, Answer Relevance). Tuy nhiên, hiện tại hệ thống đánh giá này chưa được triển khai hoàn thiện các file script chạy test cụ thể. Khuyến nghị ở giai đoạn sau cần bổ sung Benchmark Suite định lượng rõ ràng độ chính xác Intent (F1-Score) và Hallucination Rate.

### 4.3. Thảo luận
Kết quả cho thấy kiến trúc Edge AI kết hợp Local RAG là cực kỳ phù hợp và khả thi đối với bài toán giao thông công cộng. Việc áp dụng Validator cứng giúp giải quyết triệt để yếu điểm "ảo giác" (hallucination) thường thấy trên các hệ thống AI tạo sinh. Chiến lược 3 tầng hoạt động hiệu quả giúp Kiosk duy trì độ ổn định bất kể điều kiện mạng hay phần cứng yếu.

---

## CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### 5.1. Kết luận
Đồ án đã hoàn thành xuất sắc mục tiêu đề ra: Xây dựng một Trợ lý AI Kiosk Trạm xe buýt thông minh hoạt động 100% ngoại tuyến trên thiết bị biên. Giải pháp này không chỉ khắc phục nhược điểm rớt mạng của các ứng dụng truyền thống mà còn đảm bảo bảo mật dữ liệu, loại bỏ chi phí API Cloud, và mang lại trải nghiệm tương tác giọng nói, bản đồ mượt mà, trực quan cho mọi đối tượng hành khách.

### 5.2. Hạn chế
- **Thuật toán định tuyến:** Hiện tại dựa trên xử lý chuỗi danh sách điểm dừng cơ bản, chưa áp dụng các đồ thị trọng số không gian thực (A*/Dijkstra) tích hợp tọa độ GPS thực tế.
- **Tìm kiếm Semantic Search:** Module Retriever cho câu hỏi FAQ vẫn dùng thuật toán so khớp từ khóa, chưa tích hợp Vector Embeddings cục bộ.
- **Chế độ Online:** Hiện tại chủ yếu là luồng mô phỏng để đánh giá kiến trúc, chưa kết nối trực tiếp với API định vị xe theo thời gian thực ngoài thực tế.

### 5.3. Hướng phát triển
- Tích hợp mô hình Dense Vector Embeddings Cục bộ (như `bge-small-en-v1.5` hoặc `phobert-base`) kết hợp cơ sở dữ liệu SQLite-vec để nâng cấp khả năng hiểu câu hỏi phức tạp.
- Phát triển cấu trúc đồ thị mạng lưới giao thông không gian (Spatial Transit NetworkX) để tính toán đường đi tối ưu dựa trên thời gian thực tế và khoảng cách đi bộ.
- Hoàn thiện module Real-time Sync Agent (GTFS-RT) để đồng bộ vị trí xe buýt động khi Kiosk có mạng, hướng đến thương mại hóa hệ thống. Trang bị Web Dashboard cho ban quản lý để giám sát trạng thái và thu thập dữ liệu tra cứu của người dùng.
