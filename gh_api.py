"""Shared GitHub helper: repo, commit files, create release, upload asset.

Dung requests + GitHub REST API (khong can git CLI).
Token doc tu bien moi truong GITHUB_TOKEN hoac truyen truc tiep.
"""

from __future__ import annotations

import base64
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests

API = "https://api.github.com"
TIMEOUT = 60


class GHError(RuntimeError):
    pass


def _err(r) -> str:
    try:
        return r.json().get("message") or r.text[:200]
    except ValueError:
        return r.text[:200]


@dataclass
class GitHub:
    token: str
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "game-uploader",
            }
        )

    # ---------- helpers ----------

    def _call(self, method: str, url: str, **kw):
        last: Exception | None = None
        for attempt in range(3):
            try:
                r = self.session.request(method, url, timeout=TIMEOUT, **kw)
            except requests.RequestException as e:
                last = e
                time.sleep(1 + attempt)
                continue
            if r.status_code in (401, 403) and attempt < 2 and r.headers.get("X-RateLimit-Remaining") == "0":
                time.sleep(3)
                continue
            if r.status_code >= 400:
                raise GHError(f"{method} {url} -> {r.status_code}: {_err(r)}")
            return r
        raise GHError(f"khong ket noi duoc GitHub: {last}")

    def user(self) -> str:
        return self._call("GET", f"{API}/user").json()["login"]

    # ---------- repo ----------

    def repo_exists(self, full_name: str) -> bool:
        r = self.session.get(f"{API}/repos/{full_name}", timeout=TIMEOUT)
        return r.status_code == 200

    def create_repo(self, name: str, private: bool = True, description: str = "") -> dict:
        payload = {"name": name, "private": private, "auto_init": True,
                   "description": description or f"Game upload bai {name}"}
        return self._call("POST", f"{API}/user/repos", json=payload).json()

    def default_branch(self, full_name: str) -> str:
        return self._call("GET", f"{API}/repos/{full_name}").json().get("default_branch", "main")

    def sha_of(self, full_name: str, path: str, branch: str) -> str | None:
        r = self.session.get(
            f"{API}/repos/{full_name}/contents/{path}",
            params={"ref": branch}, timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()["sha"]
        return None

    # ---------- files ----------

    def put_file(self, full_name: str, path: str, data: bytes, branch: str,
                 message: str) -> dict:
        r = self._call(
            "PUT",
            f"{API}/repos/{full_name}/contents/{path}",
            params={"branch": branch},
            json={
                "message": message,
                "content": base64.b64encode(data).decode(),
                "sha": self.sha_of(full_name, path, branch),
            },
        )
        return r.json()

    def upload_tree(self, full_name: str, files: list[tuple[str, bytes]],
                    branch: str, message: str, prefix: str = "") -> int:
        """Commit nhieu file mot lan bang Git Data API. files = [(rel_path, bytes), ...]"""
        base = self._call("GET", f"{API}/repos/{full_name}/git/ref/heads/{branch}").json()
        head = base["object"]["sha"]

        tree_entries, uploaded = [], 0
        for rel, blob in files:
            r = self._call(
                "POST", f"{API}/repos/{full_name}/git/blobs",
                json={"content": base64.b64encode(blob).decode(), "encoding": "base64"},
            )
            tree_entries.append({
                "path": f"{prefix}{rel}" if prefix else rel,
                "mode": "100644",
                "type": "blob",
                "sha": r.json()["sha"],
            })
            uploaded += 1

        tree_sha = self._call(
            "POST", f"{API}/repos/{full_name}/git/trees",
            json={"base_tree": head, "tree": tree_entries},
        ).json()["sha"]

        commit = self._call(
            "POST", f"{API}/repos/{full_name}/git/commits",
            json={"message": message, "tree": tree_sha, "parents": [head]},
        ).json()

        self._call("PATCH", f"{API}/repos/{full_name}/git/refs/heads/{branch}",
                   json={"sha": commit["sha"], "force": False})
        return uploaded

    # ---------- release ----------

    def create_release(self, full_name: str, tag: str, name: str,
                       body: str = "", prerelease: bool = False) -> dict:
        # xoa tag/release cung ten neu ton tai -> tao lai cho sach
        self.session.delete(f"{API}/repos/{full_name}/releases/tags/{tag}", timeout=TIMEOUT)
        return self._call(
            "POST", f"{API}/repos/{full_name}/releases",
            json={"tag_name": tag, "name": name or tag, "body": body,
                  "prerelease": prerelease},
        ).json()

    def upload_asset(self, upload_url: str, path: str) -> str:
        """upload_url co the chua '{?name,label}' -> cat placeholder truoc."""
        target = upload_url.split("{")[0]
        p = Path(path)
        data = p.read_bytes()
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        r = self._call(
            "POST", target,
            params={"name": p.name},
            headers={"Content-Type": ctype, "Content-Length": str(len(data))},
            data=data,
        )
        return r.json()["browser_download_url"]


def collect_files(folder: Path, exclude: tuple[str, ...] = (".git", "__pycache__", ".venv")) -> list[tuple[str, bytes]]:
    """Doc file trong folder, bo qua thu muc build. Tra ve [(relative_path, bytes)]."""
    out: list[tuple[str, bytes]] = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in exclude]
        for name in files:
            fp = Path(root) / name
            try:
                out.append((str(fp.relative_to(folder)).replace("\\", "/"), fp.read_bytes()))
            except OSError:
                continue
    return out


def get_token() -> str:
    t = os.environ.get("GITHUB_TOKEN", "").strip()
    if t:
        return t
    raise GHError("Chua co token. Dat bien GITHUB_TOKEN hoac nhap token khi app yeu cau.")
