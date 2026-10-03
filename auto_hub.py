"""Auto Hub: quet game moi tren Hubcap -> check GitHub -> upload thieu.

Nguon game: GET /search?q=<tu khoa> cua Hubcap, tra ve
  game_id, game_name, header_image, uploaded_date, manifest_available

Hubcap khong co endpoint liet ke toan bo game va offset bi bo qua, nen quet
bang nhieu tu khoa roi khu trung lap theo game_id.

Luong:
  1. Doc danh sach AppID da co tren GitHub (danh sach nhanh tu branch list).
  2. Quet Hubcap theo tu khoa, loai game da co / manifest khong san.
  3. Uploader lam het luot con trong quota (mac dinh 25/ngay).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from hub_core import Hub, HubError, download_manifest, notify, steam_info

BASE = "https://hubcapmanifest.com/api/v1"
QUOTA_URL = f"{BASE}/user/stats"
SEARCH_URL = f"{BASE}/search"
MAX_LIMIT = 100  # Hubcap tu choi limit > 100

# Tu khoa quet mac dinh. Chi can 3 chu tro len.
DEFAULT_KEYWORDS = [
    "the", "game", "of", "and", "edition", "demo", "playtest",
    "remastered", "complete", "full", "premium", "deluxe",
    "collection", "bundle", "ultimate", "standard", "pro",
]


@dataclass
class Candidate:
    app_id: str
    name: str
    image: str | None = None
    uploaded: str = ""

    @property
    def is_demo(self) -> bool:
        return "demo" in self.name.lower() or "playtest" in self.name.lower()


@dataclass
class ScanResult:
    candidates: list[Candidate] = field(default_factory=list)
    github_have: set[str] = field(default_factory=set)
    skipped_no_manifest: int = 0
    keywords_used: list[str] = field(default_factory=list)


class HubcapSearch:
    """Client search Hubcap. Session dung chung de giu connection."""

    def __init__(self, keys: list[str]) -> None:
        self.keys = [k.strip() for k in keys if k and k.strip()]
        self.s = requests.Session()

    def _headers(self, key: str) -> dict:
        return {"Authorization": f"Bearer {key}"}

    def quota(self, key: str) -> dict:
        r = self.s.get(QUOTA_URL, headers=self._headers(key), timeout=20)
        r.raise_for_status()
        return r.json()

    def best_key(self) -> str | None:
        """Key con luot nhieu nhat. None = het key hoac het han."""
        best, left = None, -1
        for k in self.keys:
            try:
                q = self.quota(k)
            except requests.RequestException:
                continue
            if q.get("daily_usage") is None:
                continue
            rem = q["daily_limit"] - q["daily_usage"]
            if rem > left:
                best, left = k, rem
        return best if left > 0 else None

    def quota_left(self, key: str) -> tuple[int, int]:
        q = self.quota(key)
        return q["daily_limit"] - q["daily_usage"], q["daily_limit"]

    def search(self, key: str, keyword: str, limit: int = MAX_LIMIT) -> list[dict]:
        """Tim game theo tu khoa. Loi thi tra ve [] thay vi lam app dung lai."""
        if len(keyword) < 3:
            return []
        try:
            r = self.s.get(SEARCH_URL, headers=self._headers(key),
                           params={"q": keyword, "limit": min(limit, MAX_LIMIT)},
                           timeout=90)
        except requests.RequestException:
            return []
        if r.status_code != 200:
            return []
        try:
            return r.json().get("results") or []
        except ValueError:
            return []


# ---------------------------------------------------------------- github


def github_appids(hub: Hub) -> set[str]:
    """Doc so AppID da co tren repo. Dung branches API — 1 request/page."""
    found: set[str] = set()
    for page in range(1, 40):
        r = hub.session.get(
            f"https://api.github.com/repos/{hub.repo}/branches",
            params={"per_page": 100, "page": page}, timeout=30,
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        for b in batch:
            name = b.get("name", "")
            if name.isdigit():
                found.add(name)
        if len(batch) < 100:
            break
    return found


# ---------------------------------------------------------------- scan


def scan(search: HubcapSearch, key: str, keywords: list[str],
         have: set[str], include_demos: bool = False,
         log=print) -> ScanResult:
    """Quet Hubcap, tra ve danh sach game chua co tren GitHub."""
    res = ScanResult(github_have=set(have))
    seen: set[str] = set()

    for i, kw in enumerate(keywords, 1):
        log(f"[quet {i}/{len(keywords)}] tu khoa '{kw}'...")
        rows = search.search(key, kw)
        if not rows:
            continue
        res.keywords_used.append(kw)
        log(f"    -> {len(rows)} ket qua")

        for r in rows:
            gid = str(r.get("game_id") or "").strip()
            if not gid.isdigit() or gid in seen:
                continue
            seen.add(gid)
            if not r.get("manifest_available"):
                res.skipped_no_manifest += 1
                continue
            if gid in have:
                continue
            c = Candidate(gid, (r.get("game_name") or f"Game {gid}").strip(),
                          r.get("header_image"), r.get("uploaded_date") or "")
            if c.is_demo and not include_demos:
                continue
            res.candidates.append(c)

        time.sleep(0.3)  # khong danh sat may chu Hubcap

    # Game moi len truoc
    res.candidates.sort(key=lambda c: c.uploaded, reverse=True)
    return res


# ---------------------------------------------------------------- upload


def upload_missing(hub: Hub, cfg: dict, key: str, search: HubcapSearch,
                   candidates: list[Candidate], max_upload: int,
                   log=print) -> dict:
    """Up cac game thieu, tu dung luot con trong quota Hubcap."""
    stats = {"uploaded": 0, "skipped_no_quota": 0, "failed": 0, "limit": 0}
    out: list[dict] = []

    for i, c in enumerate(candidates, 1):
        if stats["uploaded"] >= max_upload:
            break
        try:
            left, limit = search.quota_left(key)
        except requests.RequestException:
            log("[loi] khong doc duoc quota Hubcap")
            break
        if left <= 0:
            stats["limit"] = limit
            stats["skipped_no_quota"] = len(candidates) - stats["uploaded"]
            log(f"[ dung ] het luot Hubcap ({limit}/{limit})")
            break
        if stats["uploaded"] >= limit:
            stats["skipped_no_quota"] = len(candidates) - stats["uploaded"]
            log(f"[ dung ] dat gioi han {limit} game/ngay")
            break

        log(f"[{i}/{len(candidates)}] {c.name} ({c.app_id}) — con {left} luot")
        try:
            files = download_manifest(cfg, c.app_id)
            sha = hub.push(c.app_id, files, f"Tai moi {c.name} ({c.app_id}) via Auto Hub")
            stats["uploaded"] += 1
            out.append({"app_id": c.app_id, "name": c.name, "commit": sha})
            log(f"    -> OK, commit {sha[:7]}")
            if cfg.get("discord_webhook"):
                action = "Tải mới"
                notify(cfg, action, c.name, c.app_id, file_count=len(files), image=c.image)
        except HubError as e:
            stats["failed"] += 1
            log(f"    -> LOI: {e}")
        except requests.RequestException as e:
            stats["failed"] += 1
            log(f"    -> LOI mang: {e}")

    return {"stats": stats, "uploaded": out}
