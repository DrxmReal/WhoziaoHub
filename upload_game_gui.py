#!/usr/bin/env python3
"""App 2 - GUI (tkinter): chon folder game, tao repo, commit, release.

Chay: python upload_game_gui.py
Token lay tu whoziao_config.json (neu co) hoac nhap tay trong giao dien.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from gh_api import GHError, GitHub, collect_files


def load_saved() -> dict:
    """Nap config san co (cung thu muc app, hoac thu muc cha)."""
    here = Path(__file__).parent
    for p in [here / "whoziao_config.json",
              *[up / "whoziao_config.json" for up in here.parents[:2]]]:
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return {}
    return {}


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Game Uploader - GitHub")
        self.geometry("660x540")
        self.minsize(560, 520)
        self.events: queue.Queue = queue.Queue()

        saved = load_saved()
        self.folder = tk.StringVar(value=str(Path.cwd()))
        self.token = tk.StringVar(value=saved.get("github_token", "")
                                  or os.environ.get("GITHUB_TOKEN", ""))
        self.repo = tk.StringVar(value=(saved.get("github_repo", "") or "my-game").split("/")[-1])
        self.public = tk.BooleanVar(value=False)
        self.branch = tk.StringVar()
        self.message = tk.StringVar()
        self.tag = tk.StringVar()
        self.notes = tk.StringVar()
        self.make_release = tk.BooleanVar(value=True)
        self.assets = tk.StringVar(value="Chua chon file")

        self._build()
        self.after(80, self._drain)

    # ---------- ui ----------

    def _build(self) -> None:
        pad = ttk.Frame(self, padding=12)
        pad.pack(fill="both", expand=True)

        def row(label, var, r, widget="entry"):
            ttk.Label(pad, text=label).grid(row=r, column=0, sticky="w", pady=5)
            if widget == "entry":
                w = ttk.Entry(pad, textvariable=var)
            elif widget == "spin":
                w = ttk.Entry(pad, textvariable=var)
            else:
                w = ttk.Checkbutton(pad, text=label, variable=var)
            w.grid(row=r, column=1, sticky="we", pady=5)
            return w

        pad.columnconfigure(1, weight=1)

        ttk.Label(pad, text="Thu muc game").grid(row=0, column=0, sticky="w", pady=5)
        e = ttk.Entry(pad, textvariable=self.folder)
        e.grid(row=0, column=1, sticky="we", pady=5)
        ttk.Button(pad, text="Chon...", command=self._pick_folder).grid(row=0, column=2, padx=(6, 0))

        ttk.Label(pad, text="GitHub Token (PAT)").grid(row=1, column=0, sticky="w", pady=5)
        et = ttk.Entry(pad, textvariable=self.token, show="*")
        et.grid(row=1, column=1, sticky="we", pady=5)
        ttk.Button(pad, text="Hien", command=self._toggle).grid(row=1, column=2, padx=(6, 0))
        self._token_entry = et

        row("Repo (owner/name)", self.repo, 2)
        ttk.Checkbutton(pad, text="Repo public (mac dinh private)", variable=self.public).grid(
            row=3, column=1, sticky="w", pady=5)
        row("Branch (de trong = mac dinh)", self.branch, 4)
        row("Commit message", self.message, 5)
        ttk.Checkbutton(pad, text="Tao GitHub Release", variable=self.make_release).grid(
            row=6, column=1, sticky="w", pady=5)
        row("Tag (vd v1.0.0)", self.tag, 7)
        row("Release notes", self.notes, 8)

        ttk.Label(pad, text="File dinh kem (exe/zip)").grid(row=9, column=0, sticky="w", pady=5)
        ttk.Label(pad, textvariable=self.assets).grid(row=9, column=1, sticky="we", pady=5)
        ttk.Button(pad, text="Them...", command=self._pick_assets).grid(row=9, column=2, padx=(6, 0))
        ttk.Button(pad, text="Xoa het", command=lambda: self.assets.set("Chua chon file")).grid(
            row=9, column=3, padx=(6, 0))

        self.bar = tbar = ttk.Progressbar(pad, mode="determinate")
        tbar.grid(row=10, column=0, columnspan=4, sticky="we", pady=(14, 6))

        self.log = tk.Text(pad, height=12, state="disabled", font=("Consolas", 9))
        self.log.grid(row=11, column=0, columnspan=4, sticky="nsew")
        pad.rowconfigure(11, weight=1)

        btns = ttk.Frame(pad)
        btns.grid(row=12, column=0, columnspan=4, sticky="we", pady=(10, 0))
        self.go_btn = ttk.Button(btns, text="Upload", command=self._start)
        self.go_btn.pack(side="left")
        ttk.Button(btns, text="Dong", command=self.destroy).pack(side="right")

    def _pick_folder(self) -> None:
        d = filedialog.askdirectory(initialdir=self.folder.get() or None)
        if d:
            self.folder.set(d)

    def _pick_assets(self) -> None:
        fs = filedialog.askopenfilenames(
            title="Chon file dinh kem",
            filetypes=[("Game files", "*.exe *.zip *.7z *.rar *.apk *.dmg *.tar.gz"), ("All", "*.*")],
        )
        if fs:
            self.assets.set("; ".join(Path(f).name for f in fs))
            self._asset_paths = [Path(f) for f in fs]

    def _toggle(self) -> None:
        self._token_entry.configure(show="" if self._token_entry.cget("show") else "*")

    def _p(self, msg: str) -> None:
        self.events.put(msg)

    # ---------- worker ----------

    def _start(self) -> None:
        folder = Path(self.folder.get()).expanduser()
        if not folder.is_dir():
            messagebox.showerror("Loi", "Thu muc khong ton tai")
            return
        if not self.token.get().strip():
            messagebox.showerror("Loi", "Can nhap GitHub Token")
            return

        cfg = dict(
            folder=folder,
            token=self.token.get().strip(),
            repo=self.repo.get().strip(),
            public=self.public.get(),
            branch=self.branch.get().strip(),
            message=self.message.get().strip(),
            tag=self.tag.get().strip(),
            notes=self.notes.get().strip(),
            make_release=self.make_release.get(),
            assets=list(getattr(self, "_asset_paths", [])),
        )
        self.go_btn.configure(state="disabled")
        self.bar.configure(value=0)
        threading.Thread(target=self._work, args=(cfg,), daemon=True).start()

    def _work(self, cfg: dict) -> None:
        try:
            gh = GitHub(cfg["token"])
            login = gh.user()
            self._p(f"[+] Tai khoan: {login}")

            repo = cfg["repo"] if "/" in cfg["repo"] else f"{login}/{cfg['repo']}"
            if not gh.repo_exists(repo):
                gh.create_repo(repo.split("/", 1)[1], private=not cfg["public"])
                self._p(f"[+] Da tao repo {repo}")
                time.sleep(2)
            else:
                self._p(f"[+] Repo da co: {repo}")

            branch = cfg["branch"] or gh.default_branch(repo)
            files = collect_files(cfg["folder"])
            total = sum(len(b) for _, b in files)
            self._p(f"[+] Commit {len(files)} file ({total/1024/1024:.1f} MB) -> {branch}")

            msg = cfg["message"] or f"upload {len(files)} files - {datetime.now():%Y-%m-%d %H:%M}"
            gh.upload_tree(repo, files, branch, msg, prefix="")
            self.bar.configure(value=60)
            self._p("[+] Commit xong")

            if cfg["make_release"]:
                tag = cfg["tag"] or f"v{datetime.now():%Y%m%d-%H%M%S}"
                rel = gh.create_release(repo, tag, f"{repo.split('/')[1]} {tag}", cfg["notes"])
                self.bar.configure(value=80)
                self._p(f"[+] Release {rel['html_url']}")

                assets = cfg["assets"] or [self._zip(cfg["folder"])]
                for p in assets:
                    if not p.is_file():
                        continue
                    url = gh.upload_asset(rel["upload_url"], str(p))
                    self._p(f"[+] Asset {p.name} ({p.stat().st_size/1024/1024:.1f} MB) -> {url}")
                    self.bar.configure(value=95)

            self.bar.configure(value=100)
            self._p(f"\nXong: https://github.com/{repo}")
            self.events.put(("done", True))
        except GHError as e:
            self._p(f"[LOI] {e}")
            self.events.put(("done", False))
        except Exception as e:  # noqa: BLE001
            self._p(f"[LOI] {type(e).__name__}: {e}")
            self.events.put(("done", False))

    @staticmethod
    def _zip(folder: Path) -> Path:
        import zipfile
        out = folder.parent / f"{folder.name}-source-{datetime.now():%Y%m%d-%H%M%S}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, names in os.walk(folder):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv")]
                for n in names:
                    fp = Path(root) / n
                    z.write(fp, fp.relative_to(folder))
        return out

    # ---------- ui thread ----------

    def _drain(self) -> None:
        try:
            while True:
                item = self.events.get_nowait()
                if isinstance(item, tuple) and item[0] == "done":
                    self.go_btn.configure(state="normal")
                    if item[1]:
                        messagebox.showinfo("Xong", "Upload thanh cong")
                    else:
                        messagebox.showerror("Loi", "Xem log de biet chi tiet")
                else:
                    self.log.configure(state="normal")
                    self.log.insert("end", str(item) + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._drain)


if __name__ == "__main__":
    App().mainloop()
