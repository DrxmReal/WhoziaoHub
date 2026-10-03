#!/usr/bin/env python3
"""App GUI: nhap AppID game -> tai manifest tu Hubcap -> push len GitHub.

Tuong duong /hubget, /hubupdate, /hubcheck cua bot Discord, chay truc tiep tren
may thay vi qua lenh Discord.

Chay: python hub_desktop.py
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import hub_core as hc

def _find_config() -> Path:
    """Uu tien config cung thu muc app, sau do le len thu muc cha."""
    here = Path(__file__).parent / "whoziao_config.json"
    if here.is_file():
        return here
    for up in Path(__file__).parents[1:3]:
        cand = up / "whoziao_config.json"
        if cand.is_file():
            return cand
    return here


CONFIG_FILE = _find_config()


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Whoziao Hub - Game Manager")
        self.geometry("900x660")
        self.minsize(760, 600)

        self.cfg = hc.load_config(CONFIG_FILE)
        self.events: queue.Queue = queue.Queue()
        self.results: list[dict] = []

        self.v_ids = tk.StringVar()
        self.v_token = tk.StringVar(value=self.cfg.get("github_token", ""))
        self.v_repo = tk.StringVar(value=self.cfg.get("github_repo", ""))
        self.v_webhook = tk.StringVar(value=self.cfg.get("discord_webhook", ""))
        self.v_notify = tk.BooleanVar(value=bool(self.cfg.get("discord_webhook")))
        self.v_keys = tk.StringVar()
        self.v_status = tk.StringVar(value="Chua kiem tra")

        self._build()
        self._set_keys(self.cfg.get("api_keys") or [])
        self.after(80, self._drain)

    # ---------------------------------------------------------------- ui

    def _build(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        # --- input ---
        box = ttk.LabelFrame(root, text=" Game ", padding=8)
        box.grid(row=0, column=0, sticky="we", pady=(0, 8))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="AppID game (cach nhau dau , hoac space)").grid(
            row=0, column=0, sticky="w")
        e_ids = ttk.Entry(box, textvariable=self.v_ids, font=("Consolas", 10))
        e_ids.grid(row=0, column=1, columnspan=2, sticky="we", pady=4)
        e_ids.focus_set()
        e_ids.bind("<Return>", lambda _: self._start("check"))
        e_ids.bind("<Control-Return>", lambda _: self._start("get"))

        ttk.Label(box, text="GitHub token").grid(row=1, column=0, sticky="w")
        self.e_token = ttk.Entry(box, textvariable=self.v_token, show="*")
        self.e_token.grid(row=1, column=1, sticky="we", pady=4)
        ttk.Button(box, text="Hien", width=6,
                   command=lambda: self.e_token.configure(
                       show="" if self.e_token.cget("show") else "*")).grid(
            row=1, column=2, padx=(6, 0))

        ttk.Label(box, text="Repo").grid(row=2, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.v_repo).grid(row=2, column=1, columnspan=2,
                                                       sticky="we", pady=4)

        ttk.Label(box, text="Hubcap keys (1 dong 1 key)").grid(row=3, column=0, sticky="nw")
        self.txt_keys = tk.Text(box, height=5, font=("Consolas", 8), wrap="none")
        self.txt_keys.grid(row=3, column=1, sticky="we", pady=4)
        sc = ttk.Scrollbar(box, command=self.txt_keys.yview)
        sc.grid(row=3, column=2, sticky="ns")
        self.txt_keys.configure(yscrollcommand=sc.set)

        ttk.Checkbutton(box, text="Gui thong bao Discord", variable=self.v_notify).grid(
            row=4, column=0, sticky="w")
        ttk.Label(box, text="Webhook").grid(row=5, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.v_webhook, show="*").grid(row=5, column=1,
                                                                    sticky="we", pady=4)

        # --- buttons ---
        bar = ttk.Frame(root)
        bar.grid(row=1, column=0, sticky="we", pady=(0, 8))
        self.btns = {}
        for text, cmd, style in [
            ("Tai game moi", "get", "Accent.TButton"),
            ("Cap nhat game", "update", None),
            ("Kiem tra tren GitHub", "check", None),
            ("Kiem tra Hubcap keys", "keys", None),
            ("Luu cau hinh", "save", None),
        ]:
            b = ttk.Button(bar, text=text, command=lambda c=cmd: self._start(c))
            b.pack(side="left", padx=(0, 6))
            if style:
                b.configure(style=style)
            self.btns[cmd] = b
        ttk.Button(bar, text="Xem ket qua", command=self._open_results).pack(side="right")

        self.bar = ttk.Progressbar(root, mode="indeterminate")
        self.bar.grid(row=2, column=0, sticky="we", pady=(0, 8))

        # --- log ---
        lf = ttk.LabelFrame(root, text=" Log ", padding=4)
        lf.grid(row=2, column=0, sticky="nsew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        self.log = tk.Text(lf, height=10, state="disabled", font=("Consolas", 9), wrap="word")
        self.log.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(lf, command=self.log.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=sb.set)

        stat = ttk.Label(root, textvariable=self.v_status, anchor="w")
        stat.grid(row=4, column=0, sticky="we", pady=(6, 0))
        self.results_win: tk.Toplevel | None = None

    def _set_keys(self, keys: list[str]) -> None:
        self.txt_keys.delete("1.0", "end")
        self.txt_keys.insert("1.0", "\n".join(keys))

    def _collect_keys(self) -> list[str]:
        return [ln.strip() for ln in self.txt_keys.get("1.0", "end").splitlines() if ln.strip()]

    # ---------------------------------------------------------------- worker

    def _start(self, action: str) -> None:
        if action == "save":
            self._save_cfg()
            messagebox.showinfo("Da luu", "Cau hinh da luu vao whoziao_config.json")
            return
        if action == "keys":
            self._set_busy(True, "Dang kiem tra Hubcap keys...")
            threading.Thread(target=self._work_keys, daemon=True).start()
            return

        ids = hc.parse_app_ids(self.v_ids.get())
        if not ids:
            messagebox.showerror("Loi", "Nhap it nhat mot AppID (chi so)")
            return
        if not self.v_token.get().strip():
            messagebox.showerror("Loi", "Can nhap GitHub token")
            return

        self._save_cfg(silent=True)
        cfg = hc.load_config(CONFIG_FILE)
        self._set_busy(True, f"Xu ly {len(ids)} game...")
        self.results = []
        threading.Thread(target=self._work, args=(cfg, ids, action), daemon=True).start()

    def _set_busy(self, on: bool, status: str = "") -> None:
        for b in self.btns.values():
            b.configure(state="disabled" if on else "normal")
        if on:
            self.bar.start(10)
        else:
            self.bar.stop()
            self.bar.configure(value=0)
        if status:
            self.v_status.set(status)

    def _p(self, msg: str) -> None:
        self.events.put(("log", msg))

    def _work(self, cfg: dict, ids: list[str], action: str) -> None:
        try:
            hub = hc.Hub(cfg)
            login = hub.check_login()
            self._p(f"=== Tai khoan: {login} | repo: {hub.repo} ===")

            done = ok = 0
            for aid in ids:
                done += 1
                self.v_status.set(f"[{done}/{len(ids)}] {aid}")
                try:
                    if action == "check":
                        exists = hub.branch_exists(aid)
                        name = hc.game_name(aid)
                        self._p(f"[{aid}] {name} -> "
                                f"{'DA CO tren GitHub' if exists else 'CHUA CO tren GitHub'}")
                        self.results.append({"app_id": aid, "name": name,
                                             "ok": exists, "url": f"https://github.com/{hub.repo}/tree/{aid}"})
                    else:
                        self.results.append(
                            hc.process(hub, cfg, aid, is_update=(action == "update"), log=self._p))
                        ok += 1
                except hc.HubError as e:
                    self._p(f"[{aid}] LOI: {e}")
                    self.results.append({"app_id": aid, "name": hc.game_name(aid),
                                         "ok": False, "error": str(e)})
            self._p(f"=== Xong {done}/{len(ids)}, thanh cong {ok} ===")
            self.events.put(("done", True, done, ok))
        except Exception as e:  # noqa: BLE001
            self._p(f"LOI: {type(e).__name__}: {e}")
            self.events.put(("done", False, 0, 0))

    def _work_keys(self) -> None:
        cfg = hc.load_config(CONFIG_FILE)
        cfg["api_keys"] = self._collect_keys()
        for s in hc.key_status(cfg):
            if s["ok"]:
                self._p(f"Key {s['i']}: {s['user']} — con {s['left']}/{s['limit']} hom nay")
            else:
                self._p(f"Key {s['i']}: LOI {s['msg']}")
        if not cfg["api_keys"]:
            self._p("Chua co Hubcap key nao.")
        self.events.put(("done", True, 0, 0))

    def _save_cfg(self, silent: bool = False) -> None:
        self.cfg.update({
            "github_token": self.v_token.get().strip(),
            "github_repo": self.v_repo.get().strip(),
            "api_keys": self._collect_keys(),
            "discord_webhook": self.v_webhook.get().strip() if self.v_notify.get() else "",
        })
        try:
            hc.save_config(self.cfg, CONFIG_FILE)
            if not silent:
                self._p("Da luu cau hinh.")
        except OSError as e:
            if not silent:
                messagebox.showerror("Loi", f"Khong luu duoc: {e}")

    def _open_results(self) -> None:
        if self.results_win and self.results_win.winfo_exists():
            self.results_win.lift()
            return
        w = tk.Toplevel(self)
        w.title("Ket qua")
        w.geometry("720x360")
        self.results_win = w
        ttk.Label(w, text="Double-click dong de mo tren trinh duyet", foreground="#666").pack(
            anchor="w", padx=8, pady=(8, 0))
        tree = ttk.Treeview(w, columns=("app", "name", "status"), show="headings", height=14)
        for col, head, wdt in (("app", "AppID", 100), ("name", "Ten game", 300),
                               ("status", "Ket qua", 280)):
            tree.heading(col, text=head)
            tree.column(col, width=wdt, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        for r in self.results:
            status = ("OK — " + r["files"][0] + f" +{len(r['files'])-1} file"
                      if r.get("ok") and r.get("files")
                      else "DA CO" if r.get("ok") else "CHUA CO" if "url" in r
                      else "LOI: " + r.get("error", "?"))
            tree.insert("", "end", values=(r["app_id"], r["name"], status))
        tree.bind("<Double-1>", lambda _: self._open_first_url(tree, w))

    def _open_first_url(self, tree, w) -> None:
        sel = tree.selection()
        if not sel:
            return
        aid = tree.item(sel[0], "values")[0]
        for r in self.results:
            if r["app_id"] == aid and r.get("url"):
                webbrowser.open(r["url"])
                return

    # ---------------------------------------------------------------- ui thread

    def _drain(self) -> None:
        try:
            while True:
                item = self.events.get_nowait()
                if item[0] == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", item[1] + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                else:
                    _, ok, done, good = item
                    self._set_busy(False)
                    self.v_status.set(
                        f"{datetime.now():%H:%M:%S} — xong {done} game, thanh cong {good}")
                    if not ok:
                        messagebox.showerror("Loi", "Xem log de biet chi tiet")
        except queue.Empty:
            pass
        self.after(80, self._drain)


if __name__ == "__main__":
    App().mainloop()
