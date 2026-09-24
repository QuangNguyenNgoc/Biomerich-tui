# Biomerich TUI (SolRich Fork)

Một phiên bản tái cấu trúc (refactor) và chuyển đổi giao diện sang **TUI (Terminal User Interface)** từ dự án gốc SolRich (trước đây là Biomerich) — công cụ hỗ trợ ghi nhận biome, cảnh báo Discord webhook và tự động hóa cho Sol's RNG trên Roblox.

---

## 📌 Giới thiệu về Source Code (Fork)

Dự án này là một bản **fork** từ mã nguồn SolRich / Biomerich gốc với các định hướng thay đổi chính:
- **Loại bỏ hoàn toàn Web GUI cồng kềnh**: Gỡ bỏ các thành phần UI dựa trên nền tảng web (Eel, WebView, NodeJS/React frontend) nhằm giảm thiểu triệt để dung lượng và các tiến trình chạy nền.
- **Thay thế hoàn toàn bằng TUI (Terminal User Interface)**: Xây dựng giao diện dòng lệnh trực quan, tương tác phong phú dựa trên thư viện **Textual** và **Rich**.
- **Tối ưu hóa tài nguyên**: Giảm hơn 30% mức tiêu thụ RAM và giảm tải CPU đáng kể, phù hợp cho việc vận hành liên tục (long-running) trên máy tính cá nhân.
- **Tái cấu trúc luồng dữ liệu**: Cải thiện quản lý tài khoản, cấu hình linh hoạt và đồng bộ dữ liệu thời gian thực giữa Engine và giao diện hiển thị.

---

## 🚀 Hướng dẫn Cài đặt & Sử dụng (Terminal / CLI)

Ứng dụng chạy trực tiếp bằng Python thông qua giao diện Terminal (Command Prompt, PowerShell hoặc Windows Terminal) trên Windows.

### 1. Yêu cầu hệ thống
- **Hệ điều hành**: Windows 10 / 11 (64-bit)
- **Python**: Phiên bản **Python 3.10 trở lên** (khuyến nghị **Python 3.11** hoặc **Python 3.12**)
- Quyền truy cập thông thường (không yêu cầu quyền Administrator).

### 2. Thiết lập môi trường ảo (Khuyến nghị)
Mở cửa sổ dòng lệnh tại thư mục gốc của dự án:

```powershell
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo trên Windows PowerShell:
.venv\Scripts\Activate.ps1

# Hoặc kích hoạt trên Command Prompt (cmd):
.venv\Scripts\activate.bat
```

### 3. Cài đặt các thư viện phụ thuộc (Dependencies)
Cài đặt đầy đủ các gói thư viện cần thiết đã được tối giản trong file `requirements.txt`:

```bash
pip install -r requirements.txt
```

> **Ghi chú về nhận diện chữ (OCR):** Một số tính năng như nhận diện Merchant, Auto Pop cần Tesseract OCR để đọc văn bản trên màn hình. Nếu hệ thống chưa cài đặt Tesseract, ứng dụng sẽ tự động tải và cấu hình khi chạy.

### 4. Khởi chạy ứng dụng
Sau khi hoàn tất cài đặt môi trường, khởi chạy ứng dụng TUI bằng lệnh:

```bash
python main_tui.py
```

---

## 🖥️ Các tính năng trên Giao diện TUI

Giao diện Terminal được bố cục thành các tab chức năng trực quan:
- **Dashboard**: Xem nhanh trạng thái Macro Engine, danh sách tài khoản đang hoạt động và Biome thời gian thực.
- **Accounts**: Quản lý tài khoản Roblox, trạng thái đăng nhập, liên kết VIP Server và thiết lập các module tương ứng.
- **Settings**: Cấu hình các thiết lập vận hành, ngưỡng thời gian và phím tắt (Hotkeys) tự động áp dụng ngay khi lưu.
- **Automation / Modules**: Hỗ trợ các tác vụ tự động như Auto Pop, Fishing, Merchant, Eden mode,...
- **Performance**: Điều tiết hiệu năng cửa sổ Roblox nền, tối ưu hóa mức chiếm dụng RAM và CPU.
- **Logs & Timeline**: Bảng theo dõi Activity Log, Event Log và Timeline thời gian hoạt động của từng tài khoản.
- **Webhooks**: Cấu hình các kênh Discord Webhook nhận thông báo theo định dạng Discord Components v2 hiện đại.

---

## 📜 Bản quyền & Thông tin bổ sung (License & Disclaimer)

### 1. Bản quyền mã nguồn (Source Code License)
Mã nguồn của dự án được phân phối theo giấy phép mã nguồn mở **[MIT License](LICENSE)**. Bạn được tự do sử dụng, chỉnh sửa, đóng góp và phát triển thêm theo các điều khoản của giấy phép này.

### 2. Tuyên bố về tài nguyên hình ảnh (Assets & Media)
- Toàn bộ các hình ảnh, biểu tượng (icons), ảnh động (GIFs) và ảnh thu nhỏ (thumbnails) sử dụng trong dự án (dùng cho webhook push, logo, hiển thị ảnh biome...) hiện tại được **sưu tầm và lấy ngẫu nhiên từ internet** nhằm phục vụ việc nghiên cứu, phát triển và thử nghiệm nội bộ.
- Tác giả sẽ liên tục rà soát để **bổ sung thông tin nguồn gốc / ghi công (credits & attribution)** cụ thể, hoặc **thay thế hoàn toàn bằng các tài nguyên hình ảnh do cá nhân tự thiết kế và sản xuất** trong các phiên bản cập nhật tiếp theo.

### 3. Tuyên bố từ chối trách nhiệm (Disclaimer)
Dự án là sản phẩm mã nguồn mở phi thương mại do cộng đồng người chơi phát triển, không liên kết, không được chứng thực hoặc ủy quyền bởi Roblox Corporation hay nhà phát triển game Sol's RNG. Người dùng tự chịu trách nhiệm đối với tài khoản và hành vi sử dụng của mình.
