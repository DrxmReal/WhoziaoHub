#!/usr/bin/env python3
"""App GUI: thong ke game tren GitHub + quet Hubcap + up game thieu.

Chay: python auto_hub_gui.py
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
import webbrowser
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk

import auto_hub as ah
import hub_core as hc
from hub_desktop import CONFIG_FILE, _find_config


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Whoziao Hub - Auto Upload")
        self.geometry("920x720")
        self.minsize(800, 640)

        self.cfg = hc.load_config(CONFIG_FILE)
        self.events: queue.Queue = queue.Queue()
        self.scanned: list[ah.Candidate] = []
        self.uploaded: list[dict] = []

        self.v_token = tk.StringVar(value=self.cfg.get("github_token", ""))
        self.v_repo = tk.StringVar(value=self.cfg.get("github_repo", ""))
        self.v_keys = tk.StringVar(value=self._key_text())
        self.v_keywords = tk.StringVar(value=", ".join(ah.DEFAULT_KEYWORDS))
        self.v_max = tk.StringVar(value="25")
        self.v_include_demos = tk.BooleanVar(value=False)
        self.v_notify = tk.BooleanVar(value=bool(self.cfg.get("discord_webhook")))
        self.v_status = tk.StringVar(value="San sang")
        self.v_stats = tk.StringVar(value="Chua quet")

        self._build()
        self.after(80, self._drain)

    def _key_text(self) -> str:
        return "\n".join(self.cfg.get("api_keys") or [])

    # ---------------------------------------------------------------- ui

    def _build(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        # --- thong ke ---
        stat = ttk.LabelFrame(root, text=" Trang thai ", padding=8)
        stat.grid(row=0, column=0, sticky="we", pady=(0, 8))
        stat.columnconfigure(1, weight=1)

        self.lbl_have = ttk.Label(stat, text="Game tren GitHub: —", font=("Segoe UI", 10, "bold"))
        self.lbl_have.grid(row=0, column=0, sticky="w", padx=(0, 16))
        self.lbl_quota = ttk.Label(stat, text="Quota Hubcap: —", font=("Segoe UI", 10, "bold"))
        self.lbl_quota.grid(row=0, column=1, sticky="w")

        bar = ttk.Frame(root)
        bar.grid(row=1, column=0, sticky="we", pady=(0, 8))

        ttk.Button(bar, text="1. Dem game tren GitHub",
                   command=lambda: self._start("count")).pack(side="left", padx=(0, 6))
        self.btn_scan = ttk.Button(bar, text="2. Quet Hubcap",
                                    command=lambda: self._start("scan"))
        self.btn_scan.pack(side="left", padx=(0, 6))
        self.btn_up = ttk.Button(bar, text="3. Up game thieu",
                                  command=lambda: self._start("upload"))
        self.btn_up.pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Xem danh sach", command=self._show_list).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Luu cau hinh", command=self._save).pack(side="left")

        ttk.Label(bar, textvariable=self.v_stats).pack(side="right")

        # --- log ---
        lf = ttk.LabelFrame(root, text=" Log ", padding=4)
        lf.grid(row=2, column=0, sticky="nsew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)
        self.log = tk.Text(lf, state="disabled", font=("Consolas", 9), wrap="word")
        self.log.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(lf, command=self.log.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=sb.set)

        self.bar = ttk.Progressbar(root, mode="indeterminate")
        self.bar.grid(row=3, column=0, sticky="we", pady=(8, 0))
        ttk.Label(root, textvariable=self.v_status, anchor="w").grid(
            row=4, column=0, sticky="we", pady=(4, 0))

        # --- cau hinh ---
        cfgf = ttk.LabelFrame(root, text=" Cau hinh ", padding=8)
        cfgf.grid(row=5, column=0, sticky="we", pady=(8, 0))
        cfgf.columnconfigure(1, weight=1)

        ttk.Label(cfgf, text="GitHub repo").grid(row=0, column=0, sticky="w")
        ttk.Entry(cfgf, textvariable=self.v_repo).grid(row=0, column=1, columnspan=3,
                                                        sticky="we", pady=3)

        ttk.Label(cfgf, text="GitHub token").grid(row=1, column=0, sticky="w")
        ttk.Entry(cfgf, textvariable=self.v_token, show="*").grid(row=1, column=1,
                                                                   columnspan=3,
                                                                   sticky="we", pady=3)

        ttk.Label(cfgf, text="Tu khoa quet").grid(row=2, column=0, sticky="w")
        ttk.Entry(cfgf, textvariable=self.v_keywords).grid(row=2, column=1, columnspan=3,
                                                           sticky="we", pady=3)

        ttk.Label(cfgf, text="Toi da game/ngay").grid(row=3, column=0, sticky="w")
        ttk.Entry(cfgf, textvariable=self.v_max, width=8).grid(row=3, column=1, sticky="w", pady=3)
        ttk.Checkbutton(cfgf, text="Gom ca game Demo/Playtest",
                        variable=self.v_include_demos).grid(row=3, column=2, sticky="w", padx=12)
        ttk.Checkbutton(cfgf, text="Bao Discord", variable=self.v_notify).grid(
            row=3, column=3, sticky="w")

        ttk.Label(cfgf, text="Hubcap keys").grid(row=4, column=0, sticky="nw")
        self.txt_keys = tk.Text(cfgf, height=4, font=("Consolas", 8), wrap="none")
        self.txt_keys.grid(row=4, column=1, columnspan=3, sticky="we", pady=3)
        self.txt_keys.insert("1.0", self.v_keys.get())

    def _p(self, msg: str) -> None:
        self.events.put(("log", msg))

    def _set_busy(self, on: bool) -> None:
        for b in (self.btn_scan, self.btn_up):
            b.configure(state="disabled" if on else "normal")
        self.bar.start(10) if on else self.bar.stop()

    # ---------------------------------------------------------------- run

    def _collect_keys(self) -> list[str]:
        return [x.strip() for x in self.txt_keys.get("1.0", "end").splitlines() if x.strip()]

    def _save(self) -> None:
        self.cfg.update({
            "github_token": self.v_token.get().strip(),
            "github_repo": self.v_repo.get().strip(),
            "api_keys": self._collect_keys(),
            "discord_webhook": self.cfg.get("discord_webhook", "") if self.v_notify.get() else "",
        })
        hc.save_config(self.cfg, CONFIG_FILE)
        messagebox.showinfo("Da luu", "Cau hinh da luu.")

    def _start(self, action: str) -> None:
        if action == "upload" and not self.scanned:
            messagebox.showwarning("Can quet truoc", "Bam 'Quet Hubcap' de biet game nao thieu.")
            return
        keys = self._collect_keys()
        if not keys:
            messagebox.showerror("Loi", "Can it nhat mot Hubcap key")
            return
        if not self.v_token.get().strip():
            messagebox.showerror("Loi", "Can nhap GitHub token")
            return

        self._save()
        cfg = hc.load_config(CONFIG_FILE)
        kws = [x.strip() for x in self.v_keywords.get().replace(",", " ").split() if len(x) >= 3]
        try:
            maxup = int(self.v_max.get())
        except ValueError:
            maxup = 25

        args = (cfg, keys, kws, maxup, self.v_include_demos.get(), action)
        self._set_busy(True)
        threading.Thread(target=self._work, args=args, daemon=True).start()

    def _work(self, cfg, keys, kws, maxup, demos, action) -> None:
        try:
            s = ah.HubcapSearch(keys)
            hub = hc.Hub(cfg)
            self._p(f"=== Tai khoan: {hub.check_login()} | repo: {hub.repo} ===")

            if action == "count":
                have = ah.github_appids(hub)
                self.events.put(("have", len(have)))
                self._p(f"[xong] Repo dang co {len(have)} game (AppID la branch)")
                branches = 0
                self.events.put(("done", True))
                return

            key = s.best_key()
            if not key:
                self._p("[loi] khong co Hubcap key nao con luot")
                self.events.put(("done", False))
                return
            left, limit = s.quota_left(key)
            self.events.put(("quota", (left, limit)))
            self._p(f"[quota] con {left}/{limit} luot hom nay")

            have = ah.github_appids(hub)
            self.events.put(("have", len(have)))
            self._p(f"[github] repo co {len(have)} game")

            if action == "scan":
                res = ah.scan(s, key, kws, have, include_demos=demos, log=self._p)
                self.scanned = res.candidates
                self._p(f"[xong] tim thay {len(self.scanned)} game chua co tren GitHub")
                if res.skipped_no_manifest:
                    self._p(f"       bo qua {res.skipped_no_manifest} game khong co manifest")
                self._p(f"       (quet qua {len(res.keywords_used)} tu khoa)")
                for c in self.scanned[:15]:
                    self._p(f"       - {c.app_id:10} {c.name} ({c.uploaded})")
                if len(self.scanned) > 15:
                    self._p(f"       ... va {len(self.scanned)-15} game nua")
                self.events.put(("done", True))
                return

            if action == "upload":
                if not self.scanned:
                    self._p("[loi] chua quet, khong co danh sach game thieu")
                    self.events.put(("done", False))
                    return
                r = ah.upload_missing(hub, cfg, key, s, self.scanned, maxup, log=self._p)
                st = r["stats"]
                self.uploaded = r["uploaded"]
                self._p(f"[xong] up {st['uploaded']}, loi {st['failed']}, "
                        f"con {st['skipped_no_quota']} chua up")
                if st["skipped_no_quota"]:
                    self._p(f"       (het luot ngay nay — chay lai ngay mai de up tiep)")
                self.events.put(("uploaded", st["uploaded"]))
                self.events.put(("done", True))

        except Exception as e:  # noqa: BLE001
            self._p(f"LOI: {type(e).__name__}: {e}")
            self.events.put(("done", False))

    # ---------------------------------------------------------------- list

    def _show_list(self) -> None:
        if not self.scanned:
            messagebox.showinfo("Danh sach rong", "Bam 'Quet Hubcap' truoc.")
            return
        w = tk.Toplevel(self)
        w.title(f"Game chua co tren GitHub ({len(self.scanned)})")
        w.geometry("780x520")
        ttk.Label(w, text="Double-click de mo trang Steam").pack(anchor="w", padx=8, pady=(8, 0))
        cols = ("app", "name", "uploaded")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=20)
        for c, h, wd in (("app", "AppID", 100), ("name", "Ten game", 460),
                         ("uploaded", "Ngay them", 130)):
            tree.heading(c, text=h)
            tree.column(c, width=wd, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        for c in self.scanned:
            tree.insert("", "end", values=(c.app_id, c.name, c.uploaded))
        tree.bind("<Double-1>", lambda _: self._open(tree))

    def _open(self, tree) -> None:
        sel = tree.selection()
        if sel:
            aid = tree.item(sel[0], "values")[0]
            webbrowser.open(f"https://store.steampowered.com/app/{aid}/")

    # ---------------------------------------------------------------- ui thread

    def _drain(self) -> None:
        try:
            while True:
                item = self.events.get_nowait()
                kind = item[0]
                if kind == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", item[1] + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "have":
                    self.lbl_have.configure(text=f"Game tren GitHub: {item[1]}")
                elif kind == "quota":
                    left, limit = item[1]
                    self.lbl_quota.configure(text=f"Quota Hubcap: {left}/{limit}")
                elif kind == "uploaded":
                    self.v_stats.set(f"Da up {item[1]} game")
                elif kind == "done":
                    self._set_busy(False)
                    self.v_status.set(f"{datetime.now():%H:%M:%S} — xong")
                    if not item[1]:
                        messagebox.showerror("Loi", "Xem log de biet chi tiet")
        except queue.Empty:
            pass
        self.after(80, self._drain)


if __name__ == "__main__":
    App().mainloop()
