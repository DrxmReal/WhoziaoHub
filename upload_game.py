#!/usr/bin/env python3
"""App 1 - CLI: day folder game len GitHub (repo + release).

Vi du:
  python upload_game.py --repo owner/name --path ./mygame --private
  python upload_game.py --repo owner/name --path ./build --release --tag v1.0.0
"""

from __future__ import annotations

import argparse
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

from gh_api import GHError, GitHub, collect_files, get_token


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def zip_folder(folder: Path, ignore: tuple[str, ...]) -> Path:
    out = folder.parent / f"{folder.name}-source-{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in __import__("os").walk(folder):
            dirs[:] = [d for d in dirs if d not in ignore]
            for name in files:
                fp = Path(root) / name
                z.write(fp, fp.relative_to(folder))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload folder game len GitHub")
    ap.add_argument("--repo", required=True, help="owner/name. Ten moi se duoc tao neu chua co.")
    ap.add_argument("--path", required=True, help="Thu muc chua game")
    ap.add_argument("--token", help="PAT (bo trong -> nhap an toan hoac doc GITHUB_TOKEN)")
    ap.add_argument("--public", action="store_true", help="Repo public (mac dinh private)")
    ap.add_argument("--branch", default="")
    ap.add_argument("--msg", default="")
    ap.add_argument("--release", action="store_true", help="Tao GitHub Release")
    ap.add_argument("--tag", default="")
    ap.add_argument("--asset", nargs="*", default=[], help="File dinh kem (exe/zip)")
    ap.add_argument("--release-notes", default="")
    args = ap.parse_args()

    folder = Path(args.path).resolve()
    if not folder.is_dir():
        print(f"[loi] Khong tim thay thu muc: {folder}", file=sys.stderr)
        return 2

    token = args.token or get_token()
    gh = GitHub(token)

    try:
        login = gh.user()
    except GHError as e:
        print(f"[loi] Token khong hop le: {e}", file=sys.stderr)
        print("       Tao PAT moi tai github.com/settings/tokens (scope: repo).", file=sys.stderr)
        return 1
    print(f"[+] Dung tai khoan: {login}")

    if "/" not in args.repo:
        args.repo = f"{login}/{args.repo}"

    if not gh.repo_exists(args.repo):
        name = args.repo.split("/", 1)[1]
        gh.create_repo(name, private=not args.public)
        print(f"[+] Da tao repo: {args.repo}")
        time.sleep(2)
    else:
        print(f"[+] Repo da ton tai: {args.repo}")

    branch = args.branch or gh.default_branch(args.repo)
    files = collect_files(folder)
    if not files:
        print("[loi] Thu muc rong.", file=sys.stderr)
        return 2

    total = sum(len(b) for _, b in files)
    msg = args.msg or f"upload {len(files)} files - {datetime.now():%Y-%m-%d %H:%M}"
    print(f"[+] Commit {len(files)} file ({human(total)}) -> branch '{branch}'")
    gh.upload_tree(args.repo, files, branch, msg)
    print("[+] Commit xong")

    if args.release:
        tag = args.tag or f"v{datetime.now():%Y%m%d-%H%M%S}"
        rel = gh.create_release(args.repo, tag, f"{args.repo.split('/')[1]} {tag}",
                                args.release_notes)
        print(f"[+] Release: {rel['html_url']}")
        for a in args.asset:
            p = Path(a).resolve()
            if not p.is_file():
                print(f"[!] Bo qua asset khong ton tai: {a}")
                continue
            url = gh.upload_asset(rel["upload_url"], str(p))
            print(f"[+] Asset {p.name} ({human(p.stat().st_size)}) -> {url}")
        if not args.asset:
            z = zip_folder(folder, (".git", "__pycache__", ".venv"))
            url = gh.upload_asset(rel["upload_url"], str(z))
            print(f"[+] Asset {z.name} ({human(z.stat().st_size)}) -> {url}")

    print(f"\nXong: https://github.com/{args.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
