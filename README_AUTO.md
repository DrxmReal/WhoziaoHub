# Whoziao Hub - Auto Upload

App desktop: dem game tren GitHub, quet Hubcap, up game con thieu.

```powershell
pip install requests
python auto_hub_gui.py
```

## Cach dung

Bam theo thu tu, moi nut ghi vao log:

| Nut | Vi du |
|---|---|
| **1. Dem game tren GitHub** | Doc danh sach AppID trong repo (branch ten bang AppID) |
| **2. Quet Hubcap** | Tim game tren Hubcap, loai sanh trong GitHub, ra danh sach |
| **3. Up game thieu** | Tai manifest + push game con lai, ton luot Hubcap |

Nut **Xem danh sach** hien game tim duoc, double-click mo trang Steam.

## Quota 25 lan/ngay

App tu doc `/user/stats` cua Hubcap de biet con bao lau. Khi het luot app dung ngay, khong co ban ghi. Lan sau chay se tiep tuc phan con lai.

`Toi da game/ngay` chan them mot tran an toan. Gia tri mac dinh 25 khop voi han muc Hubcap nen dat cao hon khong tac dung.

## Vi sao phai nhieu tu khoa

Hubcap khong co endpoint liet ke toan bo game, va tham so `offset` bi bo qua (luon tra ve trang dau du doi so). Quet 1 tu khoa chi thay ~100 game trong khi Hubcap co ~25.000.

App quet nhieu tu khoa roi bo trung `game_id`. Mac dinh 18 tu khoa:

```
the, game, of, and, edition, demo, playtest, remastered, complete,
full, premium, deluxe, collection, bundle, ultimate, standard, pro
```

Tach duong dan cho de do:

```
python auto_hub_gui.py   # app do
```

Tieu khoa it nhat 3 chu, tu dong bo qua tieu ngan hon.

## Bo loc

- **Manifest khong san** — `manifest_available=false` bo qua, khong ton luot.
- **Game Demo/Playtest** — mac dinh bo qua. Tick "Gom ca game Demo/Playtest" de lay.
- **Game da co** — loai bang danh sach AppID tu GitHub.

## Luu y

- Ket qua `/search` sap xep theo ngay them moi nhat, nen game moi luon len dau danh sach.
- `/search` cham (~10-20 giay), app dung 0.3 giay giua cac tu khoa.
- Config doc/ghi `whoziao_config.json` nhu `hub_desktop.py`.
