"""Core Hub: tai manifest game tu Hubcap + push len GitHub + bao Discord.

Tach tu bot_supabase.py (nguyen ban /hubget, /hubupdate, /hubcheck) de app GUI
va bot dung chung mot logic.
"""

from __future__ import annotations

import base64
import io
import json
import re
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import requests

MANIFEST_URL = "https://hubcapmanifest.com/api/v1/manifest/{app_id}"
STATS_URL = "https://hubcapmanifest.com/api/v1/user/stats"
STEAM_NAME_URL = "https://store.steampowered.com/api/appdetails?appids={app_id}"
STEAMSPY_URL = "https://steamspy.com/api.php?request=appdetails&appid={app_id}"
STEAM_IMG = "https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_hero.jpg"
STEAM_IMG_CAPSULE = "https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
TIMEOUT = 60

DEFAULT_CONFIG = {
    "github_token": "",
    "github_repo": "DrxmReal/WhoziaoHub",
    "api_keys": [],
    "discord_webhook": "",
}


class HubError(RuntimeError):
    pass


# ---------------------------------------------------------------- config


def load_config(path: str | Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    p = Path(path)
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for k, v in data.items():
                if v not in (None, "", []):
                    cfg[k] = v
        except (OSError, ValueError):
            pass
    return cfg


def save_config(cfg: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(cfg, indent=4), encoding="utf-8")


# ---------------------------------------------------------------- hubcap


def parse_app_ids(raw: str) -> list[str]:
    return [x for x in re.split(r"[,\s;]+", raw.strip()) if x.isdigit()]


_STEAM_CACHE: dict[str, dict] = {}


def steam_info(app_id: str) -> dict:
    """Ten + anh game tu Steam appdetails, fallback SteamSpy.

    URL anh phai lay tu appdetails (co hash random trong duong dan), khong
    the doan bang `/steam/apps/{id}/header.jpg` — game moi thuong tra 404.
    store.steampowered.com hay bi treo o noi bo nen co fallback SteamSpy.
    """
    app_id = str(app_id)
    if app_id in _STEAM_CACHE:
        return _STEAM_CACHE[app_id]

    info: dict = {}

    try:
        r = requests.get(STEAM_NAME_URL.format(app_id=app_id), timeout=10)
        d = r.json()
        node = d.get(app_id) or {}
        if node.get("success"):
            data = node.get("data") or {}
            info["name"] = (data.get("name") or "").strip()
            for key in ("header_image", "background"):
                u = data.get(key)
                if u and _has_real_image(u):
                    info.setdefault("image", u)
                    break
    except Exception:
        pass

    if "name" not in info or "image" not in info:
        try:
            d = requests.get(STEAMSPY_URL.format(app_id=app_id), timeout=6).json()
            name = (d.get("name") or "").strip()
            if name:
                info.setdefault("name", name)
        except Exception:
            pass

    if "image" not in info:
        for tpl in (STEAM_IMG, STEAM_IMG_CAPSULE):
            u = tpl.format(app_id=app_id)
            if _has_real_image(u):
                info["image"] = u
                break

    _STEAM_CACHE[app_id] = info
    return info


def _has_real_image(url: str) -> bool:
    """> 5KB va la anh that — anh Steam mac dinh chi ~1.5KB."""
    try:
        r = requests.get(url, timeout=10, stream=True)
        return (r.status_code == 200
                and int(r.headers.get("Content-Length") or 0) > 5000)
    except requests.RequestException:
        return False


def game_name(app_id: str) -> str:
    return steam_info(app_id).get("name") or f"Unknown Game ({app_id})"


def game_image(app_id: str) -> str | None:
    return steam_info(app_id).get("image")


def key_status(cfg: dict) -> list[dict]:
    """Trang thieu quota tung Hubcap key."""
    out = []
    for i, k in enumerate(cfg.get("api_keys") or [], 1):
        try:
            r = requests.get(STATS_URL, headers={"Authorization": f"Bearer {k}"}, timeout=10)
            if r.status_code == 200:
                d = r.json()
                out.append({
                    "i": i, "ok": True, "user": d.get("username", "?"),
                    "left": d.get("daily_limit", 0) - d.get("daily_usage", 0),
                    "limit": d.get("daily_limit", 0),
                })
            else:
                out.append({"i": i, "ok": False, "msg": f"HTTP {r.status_code}"})
        except Exception:
            out.append({"i": i, "ok": False, "msg": "khong phan hoi"})
    return out


def download_manifest(cfg: dict, app_id: str) -> dict[str, bytes]:
    """Tai manifest tu Hubcap, thu lan luot qua cac api_keys.

    Tra ve {filename: bytes} gom file trong zip + key.vdf + <app_id>.json
    (sinh tu file .lua).
    """
    files: dict[str, bytes] = {}
    lua: bytes | None = None
    last_err = ""

    for key in cfg.get("api_keys") or []:
        try:
            r = requests.get(MANIFEST_URL.format(app_id=app_id),
                             headers={"Authorization": f"Bearer {key}"},
                             timeout=TIMEOUT)
        except requests.RequestException as e:
            last_err = f"ket noi loi: {e}"
            continue

        if r.status_code == 200:
            try:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    for info in z.infolist():
                        name = info.filename.rsplit("/", 1)[-1]  # flatten duong dan
                        if not name:
                            continue
                        data = z.read(info)
                        files[name] = data
                        if name.endswith(".lua"):
                            lua = data
            except zipfile.BadZipFile:
                last_err = "manifest khong phai zip hop le"
                continue
        elif r.status_code in (401, 403, 429):
            last_err = f"key bi tu choi ({r.status_code})"
            continue
        else:
            last_err = f"khong tim thay game tren Hubcap ({r.status_code})"
            break

        if lua:
            vdf, js = parse_lua(lua)
            files["key.vdf"] = vdf.encode("utf-8")
            files[f"{app_id}.json"] = js.encode("utf-8")
        if files:
            return files
        last_err = last_err or "manifest rong"

    raise HubError(last_err or "khong tai duoc manifest")


def parse_lua(lua_bytes: bytes) -> tuple[str, str]:
    """Chuyen file .lua cua Hubcap thanh key.vdf + json depot mapping."""
    content = lua_bytes.decode("utf-8", errors="ignore")
    depots: dict[str, dict] = {}

    key_vdf = '"depots"\n{\n'
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("addappid(") and "," in line:
            parts = [p.strip(' "(),') for p in re.split(r'[,()"]', line) if p.strip(' "(),')]
            if len(parts) >= 4 and len(parts[3]) >= 32:
                key_vdf += f'\t"{parts[1]}"\n\t{{\n\t\t"DecryptionKey"\t\t"{parts[3]}"\n\t}}\n'
        elif line.startswith("setManifestid("):
            parts = [p.strip(' "(),') for p in re.split(r'[,()"]', line) if p.strip(' "(),')]
            if len(parts) >= 3:
                depots[parts[1]] = {"manifests": {"public": {"gid": parts[2]}}}
    key_vdf += "}\n"
    return key_vdf, json.dumps({"depot": depots}, indent=4)


# ---------------------------------------------------------------- github


@dataclass
class Hub:
    cfg: dict
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.session.headers.update({
            "Authorization": f"Bearer {self.cfg.get('github_token', '')}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "whoziao-hub",
        })

    def _call(self, method: str, url: str, **kw):
        r = self.session.request(method, url, timeout=TIMEOUT, **kw)
        if r.status_code >= 400:
            try:
                msg = r.json().get("message", r.text[:150])
            except ValueError:
                msg = r.text[:150]
            raise HubError(f"{method} {url.replace('https://api.github.com', '')} -> {r.status_code}: {msg}")
        return r

    def check_login(self) -> str:
        return self._call("GET", "https://api.github.com/user").json()["login"]

    def branch_exists(self, app_id: str) -> bool:
        return self.session.get(
            f"https://api.github.com/repos/{self.repo}/branches/{app_id}", timeout=15
        ).status_code == 200

    @property
    def repo(self) -> str:
        return self.cfg.get("github_repo") or DEFAULT_CONFIG["github_repo"]

    def default_branch(self) -> str:
        return self._call("GET", f"https://api.github.com/repos/{self.repo}").json()["default_branch"]

    def push(self, app_id: str, files: dict[str, bytes], message: str) -> str:
        """Push file len branch ten bang app_id. Tra ve commit sha."""
        base_url = f"https://api.github.com/repos/{self.repo}"
        head = self.default_branch()

        tree_entries = []
        for name, data in files.items():
            blob = self._call(
                "POST", f"{base_url}/git/blobs",
                json={"content": base64.b64encode(data).decode(), "encoding": "base64"},
            ).json()
            tree_entries.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})

        base_sha = self._call(
            "GET", f"{base_url}/git/ref/heads/{head}"
        ).json()["object"]["sha"]

        tree_sha = self._call(
            "POST", f"{base_url}/git/trees",
            json={"base_tree": base_sha, "tree": tree_entries},
        ).json()["sha"]

        commit_sha = self._call(
            "POST", f"{base_url}/git/commits",
            json={"message": message, "tree": tree_sha, "parents": [base_sha]},
        ).json()["sha"]

        r = self.session.get(f"{base_url}/git/ref/heads/{app_id}", timeout=15)
        if r.status_code == 200:
            self._call("PATCH", f"{base_url}/git/refs/heads/{app_id}",
                       json={"sha": commit_sha, "force": True})
        else:
            self._call("POST", f"{base_url}/git/refs",
                       json={"ref": f"refs/heads/{app_id}", "sha": commit_sha})
        return commit_sha


# ---------------------------------------------------------------- discord


def notify(cfg: dict, action: str, name: str, app_id: str,
           file_count: int = 0, image: str | None = None) -> bool:
    """Embed Discord chi hien thi thong tin game: ten, AppID, so file, anh.

    Khong danh sach file, khong link repo — app close source nen khong de lo
    duong dan GitHub ra ngoai.
    """
    url = cfg.get("discord_webhook")
    if not url:
        return False

    line = f"**{action}** · AppID `{app_id}`"
    if file_count:
        line += f"\n📦 {file_count} file"

    embed = {
        "title": f"🎮 {name}",
        "description": line,
        "color": 3447003,
        "footer": {"text": "Whoziao Hub"},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if image:
        embed["image"] = {"url": image}

    try:
        r = requests.post(url, json={"embeds": [embed]}, timeout=15)
        return r.status_code in (200, 204)
    except requests.RequestException:
        return False


# ---------------------------------------------------------------- pipeline


def process(hub: Hub, cfg: dict, app_id: str, is_update: bool, log=print) -> dict:
    """Chay tron: ten -> tai -> push -> bao Discord. Tra ve ket qua."""
    action = "Cập nhật" if is_update else "Tải mới"
    name = game_name(app_id)
    log(f"[{app_id}] {name} — {action}")
    log(f"[{app_id}] dang tai manifest tu Hubcap...")

    files = download_manifest(cfg, app_id)
    key_vdf = "key.vdf" in files
    has_json = f"{app_id}.json" in files
    log(f"[{app_id}] tai xong {len(files)} file"
        + (" (da co key.vdf)" if key_vdf else " (thieu key.vdf)")
        + (" (da co depot json)" if has_json else ""))

    msg = f"{action} {name} ({app_id}) via Desktop App"
    sha = hub.push(app_id, files, msg)
    log(f"[{app_id}] push xong, commit {sha[:7]}")

    if notify(cfg, action, name, app_id, file_count=len(files), image=game_image(app_id)):
        log(f"[{app_id}] da gui thong bao Discord")

    return {
        "app_id": app_id, "name": name, "ok": True,
        "files": sorted(files), "branch": app_id, "commit": sha,
        "url": f"https://github.com/{hub.repo}/tree/{app_id}",
    }
