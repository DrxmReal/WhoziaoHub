<div align="center">
  <img src="https://discord.com/assets/f9bb9c4af2b9c32a2c5ee0014661546d.png" alt="Discord Logo" width="100"/>
  <h1>📦 WhoziaoHub</h1>
  <p><b>Thư viện lưu trữ dữ liệu Steam Game Manifest cá nhân</b><br>Tích hợp trực tiếp với Siêu Bot tự động giải nén ZIP <b>Whoziao Depot</b></p>
</div>

<hr/>

## 🎯 Giới Thiệu
**WhoziaoHub** là một kho dữ liệu (Repository) cá nhân được sinh ra với mục đích dự phòng và lưu trữ các tệp phân quyền tải game của hệ thống Steam (`.manifest`, `.bin`, `.json`). 

Kho lưu trữ này được kết nối trực tiếp với Bot Discord **Whoziao Depot** thông qua GitHub API. Khi người dùng nhập lệnh `/game [AppID]`, Bot sẽ tự động trích xuất các tệp từ nhánh tương ứng có trong kho lưu trữ này, gom lại thành một tệp tin nén `.zip` và gửi tức thời qua Discord.

## 🛠️ Cấu Trúc Kho Lưu Trữ
Mỗi tựa game hoặc bản DLC trong kho lưu trữ này được tách biệt hoàn toàn qua **hệ thống Nhánh (Branch)** của GitHub. 
* Cơ sở dữ liệu mặc định chỉ nằm ở nhánh `main`.
* Các tệp Manifest cho từng game cụ thể nằm ở nhánh được đặt tên theo đúng số ID của App đó. (Ví dụ: The Witcher 3 có AppID là `292030` thì toàn bộ dữ liệu nằm trên nhánh mang tên `292030`).

---

## 🚀 Hướng Dẫn Push/Upload Game Lên Kho
Có 2 cách để bổ sung kho dữ liệu cho WhoziaoHub, phục vụ cho việc sử dụng từ Bot:

### 1. Upload Thủ Công Trực Tiếp Trên Web
* Vào giao diện chính của trang Github này.
* Chuyển nhánh `main` thành một nhánh mới chứa **AppID** của tựa game bạn muốn upload.
* Nhấp vào **"Add file -> Upload files"**.
* Kéo ném các file tải cấu hình `.manifest` mà bạn đã chuẩn bị vào và bấm **Commit changes**.
* Lưu ý: Không cần tạo thư mục trong nhánh. Cứ thả file ở ngoài cùng màn hình của nhánh đó.

### 2. Sử Dụng Công Cụ Tự Động (Auto Uploader)
Nếu bạn có sẵn mã nguồn của thư mục `Whoziao-Bot` chạy trên máy chủ:
* Mở thư mục code Bot lên, tạo một thư mục con tên là `upload_zone`.
* Bên trong đó, tạo tiếp một thư mục mang mã ID Game (VD: `upload_zone/99999/`).
* Cho hết file Manifest vào thư mục `99999` vừa tạo.
* Cuối cùng, chạy file Script tự động: 
  `python auto_uploader.py`
Công cụ sẽ tự động rẽ nhánh, copy file, viết commit và push lên thẳng thay bạn! Đỡ phải dùng tay chuột.

---

## 🔒 Điều Khoản và Lưu Ý (Disclaimer)
* Repository này **KHÔNG** chứa bất kỳ tệp tin bẻ khóa (cr\*ck) hoặc dữ liệu có bản quyền trực tiếp nào của nhà phát hành game (Files Game). Nó chỉ bao gồm chữ ký cơ sở dữ liệu siêu nhỏ gọn tải về từ máy chủ public của Steam.
* Thông lượng đẩy file ZIP bị giới hạn bởi API Rate Limit mặc định do Cloudflare/Discord quy định đối với mỗi Bot.

---
<div align="center">
  <i>Được bảo trì hoạt động tự chủ và trọn đời bởi Whoziao.</i>
</div>
