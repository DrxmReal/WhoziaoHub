<div align="center">
  <img src="image.png" alt="WhoziaoHub Logo" width="130"/>
  <h1>WhoziaoHub</h1>
  <p><b>Thư viện lưu trữ dữ liệu Steam Game Manifest & Cloud Depot cá nhân</b><br>
  Tự động đồng bộ và nạp game trực tiếp qua <b>Whoziao Depot Bot & SLK Unlocker</b></p>

  <p>
    <img src="https://img.shields.io/badge/Total_Branches-62%2C550%2B-blue?style=for-the-badge&logo=git" alt="Branches"/>
    <img src="https://img.shields.io/badge/Status-Online_24%2F7-brightgreen?style=for-the-badge" alt="Status"/>
    <img src="https://img.shields.io/badge/Auto_Sync-Active-orange?style=for-the-badge&logo=githubactions" alt="Auto Sync"/>
  </p>
</div>

<hr/>

## 🎯 Giới Thiệu
**WhoziaoHub** là kho lưu trữ dữ liệu Manifest cá nhân được tối ưu hóa cho hệ sinh thái **SLK Unlocker** và bot Discord **Whoziao Depot**:
- Lưu trữ các tệp phân quyền tải game của hệ thống Steam (`.manifest`, `.json`, `key.vdf`, `.lua`).
- Kết nối trực tiếp với ứng dụng **SLK Unlocker** để tự động nạp bản quyền, giải mã depot và tạo file cấu hình `.acf` trong nháy mắt.
- Tích hợp Bot Discord tự động trích xuất game, đóng gói file `.zip` và tự động cập nhật kho lưu trữ.

---

## 🎮 Game Mới Cập Nhật (Recent Uploads)
<!-- RECENT_GAMES_START -->
| Ngày cập nhật | AppID | Tên Game | Thao tác | Trạng thái |
| :---: | :---: | :--- | :---: | :---: |
| 2026-10-10 | [`4580600`](https://github.com/DrxmReal/WhoziaoHub/tree/4580600) | **Animaly Bar: NO HUMANITY!** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`4284570`](https://github.com/DrxmReal/WhoziaoHub/tree/4284570) | **Blind Box Shop Simulator** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`5155360`](https://github.com/DrxmReal/WhoziaoHub/tree/5155360) | **Hood Warfare 2** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`3090810`](https://github.com/DrxmReal/WhoziaoHub/tree/3090810) | **Truckful** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`2010030`](https://github.com/DrxmReal/WhoziaoHub/tree/2010030) | **Denizen** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`4321030`](https://github.com/DrxmReal/WhoziaoHub/tree/4321030) | **MalO On Camera Deluxxx** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`2680280`](https://github.com/DrxmReal/WhoziaoHub/tree/2680280) | **PAPERHEAD** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-10 | [`2638890`](https://github.com/DrxmReal/WhoziaoHub/tree/2638890) | **Onimusha: Way of the Sword** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-09 | [`5189090`](https://github.com/DrxmReal/WhoziaoHub/tree/5189090) | **Clean up redundant auto-uploader scripts and JSON database files** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-09 | [`4148240`](https://github.com/DrxmReal/WhoziaoHub/tree/4148240) | **Road to Empress Ⅱ** | Tải mới | `✅ Sẵn sàng` |
| 2026-10-03 | [`4833770`](https://github.com/DrxmReal/WhoziaoHub/tree/4833770) | **Spirit Route (4833770)** | Tải mới | `✅ Sẵn sàng` |
| 2026-09-07 | [`5053820`](https://github.com/DrxmReal/WhoziaoHub/tree/5053820) | **Mimic Party** | Tải mới | `✅ Sẵn sàng` |
| 2026-09-03 | [`4001890`](https://github.com/DrxmReal/WhoziaoHub/tree/4001890) | **How to Fish** | Tải mới | `✅ Sẵn sàng` |
| 2026-08-21 | [`4255580`](https://github.com/DrxmReal/WhoziaoHub/tree/4255580) | **Mouse X** | Tải mới | `✅ Sẵn sàng` |
| 2026-08-16 | [`4148670`](https://github.com/DrxmReal/WhoziaoHub/tree/4148670) | **Sex Shop Simulator: X-RAY DESIRE** | Tải mới | `✅ Sẵn sàng` |
<!-- RECENT_GAMES_END -->

> 💡 *Bảng trên được tự động cập nhật mỗi khi Bot hoặc SLK Unlocker đẩy game mới lên kho lưu trữ.*

---

## 🛠️ Cấu Trúc Kho Lưu Trữ
Mỗi tựa game hoặc bản DLC trong kho lưu trữ này được tách biệt hoàn toàn qua **hệ thống Nhánh (Branch)** của GitHub:
* Nhánh `main`: Chứa cấu hình tổng thể và bảng danh mục trạng thái.
* Nhánh con mang tên **AppID** của game (Ví dụ: ELDEN RING có AppID là `1245620` thì dữ liệu nằm tại nhánh [`1245620`](https://github.com/DrxmReal/WhoziaoHub/tree/1245620)). Mỗi nhánh game chỉ chứa các tệp thiết yếu:
  - `<appid>.json` (Cấu hình Steam `.acf`)
  - `<appid>.lua` (Script SmokeAPI / SteamTools)
  - `*.manifest` (File phân quyền Steam)
  - `key.vdf` (Key giải mã AES depot riêng của game)

---

## 🔒 Điều Khoản & Bản Quyền (Disclaimer)
* Repository này **KHÔNG** chứa bất kỳ tệp tin bẻ khóa (cr\*ck) hoặc dữ liệu có bản quyền trực tiếp nào của nhà phát hành game (Game Binaries).
* Toàn bộ tệp `.manifest` và metadata là các chữ ký phân quyền công khai từ mạng phân phối nội dung của Steam.

<div align="center">
  <sub>Được bảo trì và phát triển bởi DrxmReal. Hoạt động tự động 24/7.</sub>
</div>
