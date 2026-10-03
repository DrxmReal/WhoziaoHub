# Game Uploader - 2 app Python upload game len GitHub

Hai app doc lap, dung chung `gh_api.py`, khong can git CLI.

## Chuan bi

```powershell
pip install requests
```

Token: tao Personal Access Token tai https://github.com/settings/tokens
(scope `repo`). Khong hardcode trong code — app nho token nhap luc chay,
hoac dat bien moi truong:

```powershell
$env:GITHUB_TOKEN = "ghp_..."
```

## App 1 — CLI (`upload_game.py`)

```powershell
# commit folder game vao repo (tu tao repo neu chua co)
python upload_game.py --repo my-game --path ..\MyGame

# tao Release + dinh kem file .exe
python upload_game.py --repo owner/my-game --path ..\MyGame `
    --release --tag v1.0.0 --asset ..\build\game.exe
```

| Tham so | Y nghia |
|---|---|
| `--repo` | `owner/name`, hoac chi `ten` -> them `owner` tu dong |
| `--path` | thu muc chua game (bat buoc) |
| `--token` | PAT, bo trong -> `GITHUB_TOKEN` |
| `--public` | repo public, mac dinh private |
| `--branch` | de trong -> lay default branch cua repo |
| `--release` | tao GitHub Release sau khi commit |
| `--tag` | vd `v1.0.0`, bo trong -> timestamp |
| `--asset` | nhieu file dinh kem; bo trong -> tu zip source |
| `--release-notes` | noi dung release |

## App 2 — GUI (`upload_game_gui.py`)

```powershell
python upload_game_gui.py
```

Form nhap token (an "Hien" de xem), chon thu muc game, repo, branch, release
tag/notes, them file dinh kem. Log + progress bar ben duoi, upload chay
thread rieng nen giao dien khong tre.

## Luu y

- Commit nhieu file mot luc qua Git Data API (blob -> tree -> commit -> ref),
  ram hon loop PUT tinh file.
- `--path` nen tro toi thu muc build/game rieng. App bo qua `.git`,
  `__pycache__`, `.venv` khi quet.
- Token trong app la tam thoi, khong ghi ra dia. Neu da dan token vao chat
  hay source, nen thu hoi (Settings -> Developer settings -> revoke) va tao
  token moi.
