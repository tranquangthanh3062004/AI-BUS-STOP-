# AI Smart Bus Stop Assistant

Hệ thống  AI thông minh tại các trạm xe buýt, hỗ trợ hỏi đáp bằng giọng nói/văn bản. 

## Yêu cầu hệ thống
- Python 3.10+
- Trình duyệt Web (Chrome/Edge)
- Git (Để tải mã nguồn)

## Hướng dẫn Cài đặt

**1. Clone dự án về máy:**
```bash
git clone https://github.com/tranquangthanh3062004/AI-BUS-STOP-.git
cd "AI BUS STOP"
```

**2. Tạo môi trường ảo và cài đặt thư viện:**
Mở Terminal/Command Prompt tại thư mục dự án và chạy:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Cài đặt thư viện Playwright (Dành cho Online Web Scraper):**
```bash
playwright install
```

**4. Cấu hình biến môi trường:**
Tạo file `.env` từ file mẫu `.env.example`:
- Windows: `copy .env.example .env`
- Linux/Mac: `cp .env.example .env`
Mở file `.env` và điền các API Key cần thiết (ví dụ: Google Gemini API) và các cấu hình hệ thống khác.

## Hướng dẫn Khởi động Hệ thống

Hệ thống đã được tích hợp sẵn script tự động khởi động cho Windows.
Chỉ cần nhấp đúp vào file hoặc chạy lệnh sau trong thư mục dự án:
```bash
start.bat
```

**Quá trình khởi động sẽ thực hiện:**
1. Dọn dẹp các tiến trình cũ đang chiếm port `8000`.
2. Khởi động FastAPI Backend Server.
3. Tự động mở giao diện Kiosk UI trên trình duyệt tại địa chỉ `http://localhost:8000`.

*(Lưu ý: Không sử dụng `run_prototype.bat` vì file này thuộc về phiên bản kiến trúc cũ).*

## Cấu trúc Dự án
Dự án được chia thành các phân hệ chuyên biệt (Backend, Edge AI, Kiosk UI, Vector DB, v.v.) tuân thủ chuẩn 12-Factor App.
Vui lòng xem file [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) để biết thêm chi tiết về kiến trúc thư mục.

## Đóng góp
Khi đóng góp code, vui lòng đảm bảo bạn không commit các model AI quá nặng (file `.gguf`, `.bin`) lên repository.
