import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from config_store import ConfigStore
from theme_manager import (
    scan_themes,
    is_firefox_profile,
    detect_active_theme,
    apply_theme,
    ensure_custom_stylesheets_enabled,
    FirefoxTheme,
)

# ── warm glass palette (lyrics-extractor inspired) ───
BG = "#0a0a0f"
PANEL = "#121216"
PANEL2 = "#18181e"
CARD = "#1e1e26"
BORDER = "#2a201a"
BORDER_ACTIVE = "#3d2e1f"
ACCENT_1 = "#FF6B35"
ACCENT_2 = "#FFB347"
ACCENT_3 = "#FFD700"
SUCCESS = "#22c55e"
INFO = "#4ab0f0"
MUTED = "#8a8078"
TEXT = "#f0e6d8"
WHITE = "#ffffff"

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SM = ("Segoe UI", 9)
FONT_XS = ("Segoe UI", 8)
FONT_U = ("Segoe UI", 7, "bold")    # uppercase labels
FONT_H1 = ("Segoe UI", 20, "bold")
FONT_H2 = ("Segoe UI", 16, "bold")
FONT_H3 = ("Segoe UI", 12, "bold")


# ── glass card ───────────────────────────────────────
def glass(parent, accent=False):
    """Frosted-glass card.  accent=True draws a tricolor gradient bar at top."""
    outer = tk.Frame(parent, bg=BORDER, highlightthickness=0)
    # thin shadow layer
    sh = tk.Frame(outer, bg="#0d0d12", highlightthickness=0)
    sh.pack(fill="both", expand=True, padx=1, pady=1)
    inner = tk.Frame(sh, bg=PANEL, highlightthickness=0)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    if accent:
        gbar = tk.Frame(outer, height=3, highlightthickness=0)
        gbar.pack(fill="x", side="top")
        # three equal segments simulating a gradient
        for i, c in enumerate([ACCENT_1, ACCENT_2, ACCENT_3]):
            seg = tk.Frame(gbar, bg=c, highlightthickness=0)
            seg.place(relx=i/3, rely=0, relwidth=1/3, relheight=1)
        inner.tkraise()   # keep content on top

    outer.inner = inner
    return outer


def L(parent, text, font=FONT, fg=TEXT, bg=BG, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


# ── styled buttons ───────────────────────────────────
def _btn(parent, text, cmd, bg="#1e1e26", fg=TEXT,
         activebackground="#2a2a35", font=FONT, padx=16, pady=7):
    return tk.Button(parent, text=text, command=cmd,
                     font=font, bg=bg, fg=fg,
                     activebackground=activebackground,
                     activeforeground=fg,
                     relief="flat", borderwidth=0,
                     padx=padx, pady=pady,
                     cursor="hand2", highlightthickness=0,
                     highlightbackground=BORDER)


def btn_accent(parent, text, cmd):
    """Gradient-simulating orange button."""
    return _btn(parent, text, cmd, bg=ACCENT_1, fg="#0a0a0f",
                activebackground=ACCENT_2,
                font=FONT_BOLD)


def btn_apply(parent, text, cmd):
    """Green apply button."""
    return _btn(parent, text, cmd, bg="#1a3a2a", fg=SUCCESS,
                activebackground="#1f4a34", font=FONT_BOLD)


def btn_small(parent, text, cmd):
    return _btn(parent, text, cmd, bg="#1e1e26", fg=MUTED,
                activebackground="#2a2a35", font=FONT_SM,
                padx=12, pady=5)


def section_title(parent, text):
    """All-caps uppercase label (like .glass-title in the web design)."""
    return L(parent, text.upper(), FONT_U, MUTED, bg(parent))


def bg(parent):
    """Get the effective background colour for a parent frame."""
    c = parent
    while isinstance(c, tk.Frame | tk.Label | tk.Button):
        try:
            return c["bg"] if c["bg"] else BG
        except Exception:
            c = c.master if c.master else c
    return BG


# ── main app ──────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Firefox Theme Switcher")
        self.configure(bg=BG)

        w, h = 860, 680
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//3}")
        self.minsize(620, 480)

        self.config_store = ConfigStore(Path.cwd() / "config.json")
        self.config_store.load()
        raw = self.config_store.data.get("profile_folder", "")
        self.profile_path = Path(raw) if raw and is_firefox_profile(Path(raw)) else None
        self.themes: list[FirefoxTheme] = []
        self.active_theme: FirefoxTheme | None = None

        self._build_header()
        self._build_scroll()
        self._build_status()

        if self.profile_path:
            self._show_themes()
        else:
            self._show_picker()

    # ── persistent chrome ────────────────────────────

    def _build_header(self):
        bar = tk.Frame(self, bg=PANEL,
                       highlightbackground=BORDER,
                       highlightthickness=1, highlightcolor=BORDER)
        bar.pack(fill="x", padx=16, pady=(14, 0))
        L(bar, "Firefox Theme Switcher", FONT_H1, TEXT, PANEL
          ).pack(anchor="w", padx=20, pady=(12, 0))
        L(bar, "Switch themes in one click", FONT, MUTED, PANEL
          ).pack(anchor="w", padx=20, pady=(2, 12))

    def _build_scroll(self):
        c = tk.Frame(self, bg=BG)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        self.canvas = tk.Canvas(c, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(c, orient="vertical",
                               command=self.canvas.yview,
                               bg=PANEL, troughcolor=BG,
                               activebackground=BORDER_ACTIVE,
                               elementborderwidth=0, borderwidth=0)
        self.body = tk.Frame(self.canvas, bg=BG)

        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(
                           scrollregion=self.canvas.bbox("all")))
        self._body_id = self.canvas.create_window(
            (0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)

        def _resize_body(e):
            self.canvas.itemconfig(self._body_id, width=e.width)
        self.canvas.bind("<Configure>", _resize_body)

        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def _wheel(e):
            self.canvas.yview_scroll(
                -1 if e.delta > 0 or e.num == 4 else 1, "units")
        self.canvas.bind_all("<MouseWheel>", _wheel)
        self.canvas.bind_all("<Button-4>", _wheel)
        self.canvas.bind_all("<Button-5>", _wheel)

    def _build_status(self):
        bar = tk.Frame(self, bg=PANEL,
                       highlightbackground=BORDER,
                       highlightthickness=1, highlightcolor=BORDER)
        bar.pack(fill="x", side="bottom", padx=16, pady=(0, 14))
        self.status_var = tk.StringVar(value="Ready")
        L(bar, "", FONT_SM, MUTED, PANEL, textvariable=self.status_var
          ).pack(side="left", padx=16, pady=6)

    # ── profile picker ───────────────────────────────

    def _show_picker(self):
        self._clear()

        col = tk.Frame(self.body, bg=BG)
        col.pack(expand=True, pady=50)

        L(col, "🔥", ("Segoe UI", 44), bg=BG).pack()
        L(col, "Select your Firefox profile",
          FONT_H2, TEXT, BG).pack(pady=(6, 2))
        L(col, "Point me to your Firefox profile folder",
          FONT, MUTED, BG).pack()

        # ── input card ────────────────────────────
        card = glass(col, accent=True)
        card.pack(fill="x", pady=(18, 0))

        section_title(card.inner, "Profile folder").pack(anchor="w", padx=16,
                                                          pady=(14, 2))

        self.picker_var = tk.StringVar(
            value=str(self.profile_path) if self.profile_path else "")
        entry = tk.Entry(card.inner,
                         textvariable=self.picker_var,
                         font=FONT, fg=TEXT,
                         bg="#0a0a10",
                         insertbackground=TEXT,
                         relief="flat",
                         highlightbackground=BORDER,
                         highlightthickness=1)
        entry.pack(fill="x", padx=14, pady=(0, 8), ipady=6)

        row = tk.Frame(card.inner, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(0, 14))
        _btn(row, "Browse Folder…", self._browse).pack(side="left", padx=(0, 8))
        btn_accent(row, "Save Profile", self._save_picker).pack(side="left")

        # ── tutorial card ─────────────────────────
        tut = glass(col)
        tut.pack(fill="x", pady=(10, 0))

        section_title(tut.inner, "How to find it").pack(anchor="w", padx=16,
                                                         pady=(12, 2))
        L(tut.inner, "Open Firefox →  about:support  in the address bar",
          FONT_SM, MUTED, PANEL).pack(anchor="w", padx=16, pady=(0, 1))
        L(tut.inner, "Look for 'Profile Folder' under 'Application Basics'",
          FONT_SM, MUTED, PANEL).pack(anchor="w", padx=16, pady=(0, 1))
        L(tut.inner, "Click the 'Open Folder' button and copy the path",
          FONT_SM, MUTED, PANEL).pack(anchor="w", padx=16, pady=(0, 1))
        L(tut.inner, "", bg=PANEL).pack(pady=(0, 12))

    def _browse(self):
        d = filedialog.askdirectory(title="Choose Firefox profile folder")
        if d:
            self.picker_var.set(d)

    def _save_picker(self):
        raw = self.picker_var.get().strip()
        if not raw:
            return
        p = Path(raw)
        if not is_firefox_profile(p):
            messagebox.showerror(
                "Invalid profile",
                "That does not look like a Firefox profile.\n"
                "Make sure it contains  prefs.js.")
            return
        self.profile_path = p
        self.config_store.set_profile_folder(str(p))
        self._show_themes()

    # ── themes view ──────────────────────────────────

    def _show_themes(self):
        self._clear()

        # profile card
        bar = glass(self.body)
        bar.pack(fill="x", pady=(0, 10))

        L(bar.inner, f"📁  {self.profile_path.name}",
          FONT_BOLD, TEXT, PANEL
          ).pack(side="left", padx=14, pady=10)

        for txt, cmd in [
            ("Change Profile", self._change_profile),
            ("Open Chrome", self._open_dir),
            ("Open Themes", self._open_themes),
        ]:
            btn_small(bar.inner, txt, cmd).pack(side="left", padx=2, pady=10)

        btn_small(bar.inner, "🔄  Refresh", self._scan
                  ).pack(side="right", padx=14, pady=10)

        self._scan()

    def _change_profile(self):
        self.profile_path = None
        self.config_store.set_profile_folder("")
        self._show_picker()

    def _open_dir(self):
        p = self.profile_path / "chrome"
        p.mkdir(exist_ok=True)
        try:
            import os; os.startfile(str(p))
        except Exception:
            self._set_status("Could not open Explorer.")

    def _open_themes(self):
        p = Path.cwd() / "themes"
        p.mkdir(exist_ok=True)
        try:
            import os; os.startfile(str(p))
        except Exception:
            self._set_status("Could not open Explorer.")

    def _scan(self):
        root = Path.cwd() / self.config_store.data.get("theme_folder", "themes")
        root.mkdir(exist_ok=True)
        self.themes = scan_themes(root)
        self.active_theme = (
            detect_active_theme(self.profile_path, self.themes)
            if self.profile_path
            else None
        )
        self._render()

    def _render(self):
        for c in list(self.body.winfo_children())[1:]:
            c.destroy()

        if not self.themes:
            self._empty_state()
            return

        hdr = tk.Frame(self.body, bg=BG)
        hdr.pack(fill="x", pady=(0, 6))
        L(hdr, f"Themes  ·  {len(self.themes)}", FONT_H3, TEXT, BG
          ).pack(anchor="w")

        for t in self.themes:
            self._card(t)

    def _card(self, t: FirefoxTheme):
        is_active = self.active_theme is not None and self.active_theme.name == t.name
        # Use a green border for the active card
        border_color = SUCCESS if is_active else BORDER
        outer = tk.Frame(self.body, bg=border_color, highlightthickness=0)
        sh = tk.Frame(outer, bg="#0d0d12", highlightthickness=0)
        sh.pack(fill="both", expand=True, padx=1, pady=1)
        inner = tk.Frame(sh, bg=PANEL, highlightthickness=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        # gradient accent bar
        gbar = tk.Frame(outer, height=3, highlightthickness=0)
        gbar.pack(fill="x", side="top")
        if is_active:
            # solid green bar for active
            seg = tk.Frame(gbar, bg=SUCCESS, highlightthickness=0)
            seg.place(relx=0, rely=0, relwidth=1, relheight=1)
        else:
            for i, c in enumerate([ACCENT_1, ACCENT_2, ACCENT_3]):
                seg = tk.Frame(gbar, bg=c, highlightthickness=0)
                seg.place(relx=i/3, rely=0, relwidth=1/3, relheight=1)
        inner.tkraise()
        card = outer
        card.pack(fill="x", pady=4)

        # name row with active badge
        name_row = tk.Frame(inner, bg=PANEL)
        name_row.pack(fill="x", padx=16, pady=(12, 2))
        section_title(inner, t.name).pack_forget()
        L(name_row, t.name.upper(), FONT_U, MUTED, PANEL
          ).pack(side="left")
        if is_active:
            badge = tk.Label(name_row, text="ACTIVE",
                             font=("Segoe UI", 7, "bold"),
                             fg="#0a0a0f", bg=SUCCESS,
                             padx=6, pady=1)
            badge.pack(side="left", padx=(8, 0))

        fi = tk.Frame(inner, bg=PANEL)
        fi.pack(anchor="w", padx=16, pady=(0, 6))
        for has, label in [
            (t.has_user_chrome, "userChrome.css"),
            (t.has_user_content, "userContent.css"),
        ]:
            fg = SUCCESS if has else MUTED
            ch = "✓" if has else "✗"
            L(fi, f"{ch}  {label}", FONT_SM, fg, PANEL
              ).pack(side="left", padx=(0, 16))

        ar = tk.Frame(inner, bg=PANEL)
        ar.pack(fill="x", padx=16, pady=(4, 12))
        btn_apply(ar, "Apply Theme", lambda t=t: self._apply(t)).pack(side="left")
        L(ar, "Restart Firefox after applying", FONT_XS, MUTED, PANEL
          ).pack(side="left", padx=(12, 0))

        # source URL — click to edit
        sr = tk.Frame(inner, bg=PANEL)
        sr.pack(fill="x", padx=16, pady=(0, 10))

        _editing = False

        def _save_url(new_url: str):
            src_path = t.folder / "source"
            if new_url:
                src_path.write_text(new_url.strip() + "\n", encoding="utf-8")
            elif src_path.exists():
                src_path.unlink()
            self.after_idle(self._scan)

        def _start_edit():
            nonlocal _editing
            if _editing:
                return
            _editing = True
            url_label.pack_forget()
            edit_entry.delete(0, "end")
            edit_entry.insert(0, t.source_url or "")
            edit_entry.pack(side="left", fill="x", expand=True, ipady=3)
            save_btn.pack(side="left", padx=(6, 0))
            edit_entry.focus_set()

        def _finish_edit(event=None):
            nonlocal _editing
            if not _editing:
                return
            _editing = False
            new_val = edit_entry.get().strip()
            edit_entry.pack_forget()
            save_btn.pack_forget()
            url_label.pack(side="left")
            if new_val != (t.source_url or ""):
                _save_url(new_val)

        def _cancel_edit(event=None):
            nonlocal _editing
            if not _editing:
                return
            _editing = False
            edit_entry.pack_forget()
            save_btn.pack_forget()
            url_label.pack(side="left")

        url_label = L(sr, "🔗  " + (t.source_url or "Add GitHub link…"),
                      FONT_XS, MUTED if t.source_url else "#4a4238", PANEL,
                      cursor="hand2")
        url_label.pack(side="left")
        url_label.bind("<Button-1>", lambda e: _start_edit())

        edit_entry = tk.Entry(sr, font=FONT_SM, fg=TEXT, bg="#0a0a10",
                              insertbackground=TEXT, relief="flat",
                              highlightbackground=BORDER, highlightthickness=1)
        edit_entry.bind("<Return>", _finish_edit)
        edit_entry.bind("<FocusOut>", _finish_edit)
        edit_entry.bind("<Escape>", _cancel_edit)

        save_btn = _btn(sr, "Save", _finish_edit,
                        bg="#1a2a1a", fg=SUCCESS,
                        activebackground="#1f3a1f",
                        font=("Segoe UI", 8, "bold"), padx=10, pady=3)

    def _empty_state(self):
        ec = glass(self.body)
        ec.pack(fill="x", pady=30)
        L(ec.inner, "📂  No themes found", FONT_H3, TEXT, PANEL
          ).pack(pady=(30, 6))
        L(ec.inner, "Drop Firefox theme folders into:",
          FONT_SM, MUTED, PANEL).pack()
        L(ec.inner, str(Path.cwd() / "themes"),
          FONT_XS, MUTED, PANEL).pack()
        L(ec.inner,
          "Each folder must contain  userChrome.css  and/or  userContent.css",
          FONT_SM, MUTED, PANEL).pack(pady=(0, 30))

    # ── apply ────────────────────────────────────────

    def _apply(self, theme):
        if not self.profile_path:
            return
        try:
            ensure_custom_stylesheets_enabled(self.profile_path)
            backup = apply_theme(self.profile_path, theme)
            # re-detect which theme is active now
            self.active_theme = detect_active_theme(
                self.profile_path, self.themes
            )
            self._render()
            self._set_status(
                f"✅  Applied '{theme.name}'.  "
                f"Backup: {backup}  |  Restart Firefox.")
        except Exception as exc:
            self._set_status(f"❌  Apply failed: {exc}")

    # ── helpers ──────────────────────────────────────

    def _clear(self):
        for c in self.body.winfo_children():
            c.destroy()

    def _set_status(self, msg):
        self.status_var.set(msg)


if __name__ == "__main__":
    App().mainloop()
