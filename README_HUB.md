# Whoziao Hub Desktop

App desktop tach tu `/hubget`, `/hubupdate`, `/hubcheck` cua bot Discord. Chay
 truc tiep tren may, khong can go qua lenh Discord.

```powershell
pip install requests
python hub_desktop.py
```

## Dung

1. **AppID game** — nhip nhau `1234, 5678 8901` (Enter = kiem tra, Ctrl+Enter = tai game).
2. **GitHub token** — PAT scope `repo`.
3. **Repo** — mac dinh `DrxmReal/WhoziaoHub`.
4. **Hubcap keys** — 1 dong 1 key.
5. **Webhook** — bat len de gui embed Discord, tick "Luu cau hinh" de nho.

Nut:

| Nut | Vi du lenh Discord |
|---|---|
| Tai game moi | `/hubget` |
| Cap nhat game | `/hubupdate` |
| Kiem tra tren GitHub | `/hubcheck` |
| Kiem tra Hubcap keys | `/hubstatus` |

## Luu dong

- Ten game lay tu Steam `appdetails`, fallback `Unknown Game (id)` khi Steam
  khong phan hoi.
- Manifest tai tu `hubcapmanifest.com`, thu lan luot qua cac key cho den khi
  mot key tra ve 200.
- File `.lua` trong manifest duoc parse thanh `key.vdf` + `<app_id>.json`
  (depot mapping) truoc khi push.
- Push vao branch trung ten AppID. Game da co branch -> force update; chua co
  -> tao branch moi tu `main`.
- Config doc tu `whoziao_config.json` (ke ca thu muc cha `key/`). Token/key
  duoc luu o day nen **khong push file nay len GitHub**.
