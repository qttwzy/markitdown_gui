import os
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
from typing import Optional, List, Dict

from tkinterdnd2 import DND_FILES, TkinterDnD

from converter import ConversionEngine, ConversionResult, normalize_path, validate_file
from predictor import ConversionPredictor, PredictionResult
from i18n import t, get_lang, set_lang, LANG_ZH, LANG_EN

logger = logging.getLogger("markitdown_gui")

COLORS = {
    "bg": "#F5F5F5",
    "surface": "#FFFFFF",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "success": "#16A34A",
    "warning": "#D97706",
    "error": "#DC2626",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "border": "#D1D5DB",
    "drop_zone": "#EFF6FF",
    "drop_zone_border": "#93C5FD",
    "drop_zone_active": "#DBEAFE",
    "timer": "#7C3AED",
    "predict": "#0891B2",
}

SORT_ASC = "asc"
SORT_DESC = "desc"
SORT_NONE = "none"

SORTABLE_COLUMNS = {"filename", "size", "predicted"}
SORT_ARROW = {SORT_ASC: " ▲", SORT_DESC: " ▼", SORT_NONE: ""}

BTN_START_NORMAL = "#2563EB"
BTN_START_HOVER = "#1D4ED8"
BTN_START_ACTIVE = "#1E40AF"
BTN_START_DISABLED = "#93C5FD"
BTN_START_TEXT = "#FFFFFF"
BTN_STOP_NORMAL = "#DC2626"
BTN_STOP_HOVER = "#B91C1C"
BTN_STOP_ACTIVE = "#991B1B"
BTN_STOP_DISABLED = "#FCA5A5"
BTN_BROWSE_NORMAL = "#4B5563"
BTN_BROWSE_HOVER = "#374151"
BTN_BROWSE_ACTIVE = "#1F2937"


class MarkItDownApp:
    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        self.root.geometry("880x780")
        self.root.minsize(800, 700)
        self.root.configure(bg=COLORS["bg"])

        self.engine = ConversionEngine()
        self.predictor = ConversionPredictor()
        self._file_list: List[str] = []
        self._file_meta: Dict[str, Dict] = {}
        self._converting = False
        self._stop_requested = False
        self._timer_start: Optional[float] = None
        self._timer_id: Optional[str] = None

        self._sort_column: str = "index"
        self._sort_direction: str = SORT_NONE

        self._setup_styles()
        self._build_ui()
        self._setup_dnd()
        self._apply_language()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("TFrame", background=COLORS["bg"])
        self.style.configure("Surface.TFrame", background=COLORS["surface"])
        self.style.configure(
            "TLabel", background=COLORS["bg"],
            foreground=COLORS["text"], font=("Microsoft YaHei UI", 10),
        )
        self.style.configure(
            "Title.TLabel", background=COLORS["bg"],
            foreground=COLORS["text"], font=("Microsoft YaHei UI", 16, "bold"),
        )
        self.style.configure(
            "Status.TLabel", background=COLORS["bg"],
            foreground=COLORS["text_secondary"], font=("Microsoft YaHei UI", 11),
        )
        self.style.configure(
            "Success.TLabel", background=COLORS["bg"],
            foreground=COLORS["success"], font=("Microsoft YaHei UI", 11),
        )
        self.style.configure(
            "Error.TLabel", background=COLORS["bg"],
            foreground=COLORS["error"], font=("Microsoft YaHei UI", 11),
        )
        self.style.configure(
            "Warning.TLabel", background=COLORS["bg"],
            foreground=COLORS["warning"], font=("Microsoft YaHei UI", 11),
        )
        self.style.configure(
            "Timer.TLabel", background=COLORS["bg"],
            foreground=COLORS["timer"], font=("Consolas", 14, "bold"),
        )
        self.style.configure(
            "Predict.TLabel", background=COLORS["bg"],
            foreground=COLORS["predict"], font=("Microsoft YaHei UI", 10),
        )
        self.style.configure(
            "Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.style.configure(
            "FileList.Treeview",
            background=COLORS["surface"], foreground=COLORS["text"],
            fieldbackground=COLORS["surface"], rowheight=26,
            font=("Consolas", 9),
        )
        self.style.configure(
            "FileList.Treeview.Heading",
            font=("Microsoft YaHei UI", 9, "bold"),
            background=COLORS["bg"], foreground=COLORS["text"],
        )
        self.style.map(
            "FileList.Treeview",
            background=[("selected", COLORS["primary"])],
            foreground=[("selected", "white")],
        )
        self.style.map(
            "FileList.Treeview.Heading",
            background=[("active", COLORS["border"])],
        )

    def _build_ui(self):
        outer = ttk.Frame(self.root)
        outer.pack(fill=tk.BOTH, expand=True)

        self._build_fixed_top(outer)
        self._build_scrollable_area(outer)

    def _build_fixed_top(self, parent):
        self.top_frame = ttk.Frame(parent, padding=(16, 16, 16, 0))
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        title_row = ttk.Frame(self.top_frame)
        title_row.pack(fill=tk.X, pady=(0, 12))

        self.title_label = ttk.Label(title_row, text="", style="Title.TLabel")
        self.title_label.pack(side=tk.LEFT)

        self.lang_var = tk.StringVar(value=get_lang())
        lang_frame = ttk.Frame(title_row)
        lang_frame.pack(side=tk.RIGHT)
        self.lang_zh_rb = tk.Radiobutton(
            lang_frame, text="中文", variable=self.lang_var,
            value=LANG_ZH, command=self._on_language_change,
            bg=COLORS["bg"], activebackground=COLORS["bg"],
            font=("Microsoft YaHei UI", 9), selectcolor=COLORS["bg"],
        )
        self.lang_zh_rb.pack(side=tk.LEFT, padx=(0, 4))
        self.lang_en_rb = tk.Radiobutton(
            lang_frame, text="EN", variable=self.lang_var,
            value=LANG_EN, command=self._on_language_change,
            bg=COLORS["bg"], activebackground=COLORS["bg"],
            font=("Microsoft YaHei UI", 9), selectcolor=COLORS["bg"],
        )
        self.lang_en_rb.pack(side=tk.LEFT)

        self._build_drop_zone(self.top_frame)
        self._build_path_input(self.top_frame)

    def _on_language_change(self):
        new_lang = self.lang_var.get()
        set_lang(new_lang)
        self._apply_language()

    def _apply_language(self):
        self.root.title(t("app_title"))
        self.title_label.configure(text=t("title_label"))
        self.drop_label.configure(text=t("drop_text"))
        self.drop_sub.configure(text=t("drop_sub"))
        self.path_label.configure(text=t("path_label"))
        self.add_btn.configure(text=t("add_btn"))
        self.file_list_frame.configure(text=f" {t('file_list_frame')} ")
        self.file_tree.heading("index", text=t("col_index"))
        self.file_tree.heading("filename", text=t("col_filename"), command=lambda: self._on_column_click("filename"))
        self.file_tree.heading("size", text=t("col_size"), command=lambda: self._on_column_click("size"))
        self.file_tree.heading("predicted", text=t("col_predicted"), command=lambda: self._on_column_click("predicted"))
        self.file_tree.heading("path", text=t("col_path"))
        self.remove_btn.configure(text=t("remove_selected"))
        self.clear_list_btn.configure(text=t("clear_list"))
        self.pred_frame.configure(text=f" {t('prediction_frame')} ")
        self.convert_btn.configure(text=t("start_btn"))
        self.stop_btn.configure(text=t("stop_btn"))
        self.browse_btn.configure(text=t("browse_btn"))
        self.history_frame.configure(text=f" {t('history_frame')} ")
        self.history_tree.heading("time", text=t("col_time"))
        self.history_tree.heading("source", text=t("col_source"))
        self.history_tree.heading("status", text=t("col_status"))
        self.history_tree.heading("duration", text=t("col_duration"))
        self.history_tree.heading("predicted", text=t("col_pred_time"))
        self.history_tree.heading("error", text=t("col_error"))
        self.refresh_history_btn.configure(text=t("refresh_history"))
        self.clear_history_btn.configure(text=t("clear_history"))

        self._update_heading_arrows()
        self._update_prediction_panel()
        self._update_status_label()
        self._refresh_file_list_labels()
        self._refresh_history()

    def _build_scrollable_area(self, parent):
        self.scroll_container = ttk.Frame(parent)
        self.scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.scroll_canvas = tk.Canvas(
            self.scroll_container, bg=COLORS["bg"],
            highlightthickness=0, bd=0,
        )
        self.scroll_vbar = ttk.Scrollbar(
            self.scroll_container, orient=tk.VERTICAL,
            command=self.scroll_canvas.yview,
        )
        self.scroll_canvas.configure(yscrollcommand=self.scroll_vbar.set)

        self.scroll_vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll_inner = ttk.Frame(self.scroll_canvas, padding=(16, 0, 16, 16))
        self.scroll_window = self.scroll_canvas.create_window(
            (0, 0), window=self.scroll_inner, anchor=tk.NW,
        )

        self.scroll_canvas.bind("<Configure>", self._on_scroll_canvas_configure)
        self.scroll_inner.bind("<Configure>", self._on_scroll_inner_configure)
        self.scroll_canvas.bind("<Enter>", self._bind_mousewheel)
        self.scroll_canvas.bind("<Leave>", self._unbind_mousewheel)

        self._build_file_list(self.scroll_inner)
        self._build_prediction_panel(self.scroll_inner)
        self._build_status_area(self.scroll_inner)
        self._build_action_buttons(self.scroll_inner)
        self._build_history_area(self.scroll_inner)

    def _on_scroll_canvas_configure(self, event):
        self.scroll_canvas.itemconfig(self.scroll_window, width=event.width)

    def _on_scroll_inner_configure(self, event):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _bind_mousewheel(self, event):
        self.scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scroll_canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.scroll_canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event):
        self.scroll_canvas.unbind_all("<MouseWheel>")
        self.scroll_canvas.unbind_all("<Button-4>")
        self.scroll_canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    def _build_drop_zone(self, parent):
        frame = ttk.Frame(parent, style="Surface.TFrame")
        frame.pack(fill=tk.X, pady=(0, 10))

        self.drop_frame = tk.Frame(
            frame, bg=COLORS["drop_zone"], highlightbackground=COLORS["drop_zone_border"],
            highlightthickness=2, relief=tk.FLAT, padx=20, pady=18,
        )
        self.drop_frame.pack(fill=tk.X, padx=8, pady=8)

        self.drop_icon = ttk.Label(
            self.drop_frame, text="📂", font=("Segoe UI Emoji", 24),
            background=COLORS["drop_zone"], foreground=COLORS["primary"],
        )
        self.drop_icon.pack()

        self.drop_label = ttk.Label(
            self.drop_frame, text="",
            background=COLORS["drop_zone"], foreground=COLORS["text_secondary"],
            font=("Microsoft YaHei UI", 10),
        )
        self.drop_label.pack(pady=(4, 0))

        self.drop_sub = ttk.Label(
            self.drop_frame, text="",
            background=COLORS["drop_zone"], foreground=COLORS["text_secondary"],
            font=("Microsoft YaHei UI", 8),
        )
        self.drop_sub.pack(pady=(2, 0))

        self.drop_frame.bind("<Button-1>", lambda e: self._browse_files())
        self.drop_label.bind("<Button-1>", lambda e: self._browse_files())
        self.drop_icon.bind("<Button-1>", lambda e: self._browse_files())

    def _build_path_input(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 10))

        self.path_label = ttk.Label(frame, text="")
        self.path_label.pack(side=tk.LEFT, padx=(0, 6))

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(frame, textvariable=self.path_var, font=("Consolas", 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.path_entry.bind("<Return>", lambda e: self._add_path())

        self.add_btn = ttk.Button(frame, text="", command=self._add_path)
        self.add_btn.pack(side=tk.LEFT)

    def _build_file_list(self, parent):
        self.file_list_frame = ttk.LabelFrame(parent, text="", padding=8)
        self.file_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tree_frame = ttk.Frame(self.file_list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("index", "filename", "size", "predicted", "path")
        self.file_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            selectmode="extended", style="FileList.Treeview", height=8,
        )

        self.file_tree.heading("index", text="#")
        self.file_tree.heading("filename", text="", command=lambda: self._on_column_click("filename"))
        self.file_tree.heading("size", text="", command=lambda: self._on_column_click("size"))
        self.file_tree.heading("predicted", text="", command=lambda: self._on_column_click("predicted"))
        self.file_tree.heading("path", text="")

        self.file_tree.column("index", width=36, minwidth=30, anchor=tk.CENTER, stretch=False)
        self.file_tree.column("filename", width=190, minwidth=120)
        self.file_tree.column("size", width=80, minwidth=70, anchor=tk.E, stretch=False)
        self.file_tree.column("predicted", width=80, minwidth=60, anchor=tk.E, stretch=False)
        self.file_tree.column("path", width=280, minwidth=100)

        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self.file_list_frame)
        btn_frame.pack(fill=tk.X, pady=(6, 0))

        self.count_label = ttk.Label(btn_frame, text="", foreground=COLORS["text_secondary"])
        self.count_label.pack(side=tk.LEFT)

        self.total_size_label = ttk.Label(btn_frame, text="", foreground=COLORS["text_secondary"])
        self.total_size_label.pack(side=tk.LEFT, padx=(16, 0))

        self.remove_btn = ttk.Button(btn_frame, text="", command=self._remove_selected)
        self.remove_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.clear_list_btn = ttk.Button(btn_frame, text="", command=self._clear_list)
        self.clear_list_btn.pack(side=tk.RIGHT)

    def _build_prediction_panel(self, parent):
        self.pred_frame = ttk.LabelFrame(parent, text="", padding=8)
        self.pred_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(self.pred_frame)
        row1.pack(fill=tk.X)

        self.pred_total_label = ttk.Label(
            row1, text="", style="Predict.TLabel",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.pred_total_label.pack(side=tk.LEFT)

        self.pred_range_label = ttk.Label(
            row1, text="", style="Predict.TLabel",
            font=("Microsoft YaHei UI", 9),
        )
        self.pred_range_label.pack(side=tk.LEFT, padx=(16, 0))

        self.pred_confidence_label = ttk.Label(
            row1, text="", foreground=COLORS["text_secondary"],
            font=("Microsoft YaHei UI", 9),
        )
        self.pred_confidence_label.pack(side=tk.RIGHT)

        row2 = ttk.Frame(self.pred_frame)
        row2.pack(fill=tk.X, pady=(4, 0))

        self.pred_detail_label = ttk.Label(
            row2, text="", foreground=COLORS["text_secondary"],
            font=("Microsoft YaHei UI", 9),
        )
        self.pred_detail_label.pack(side=tk.LEFT)

    def _build_status_area(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 8))

        self.status_label = ttk.Label(frame, text="", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)

        self.timer_label = ttk.Label(frame, text="⏱ 00:00", style="Timer.TLabel")
        self.timer_label.pack(side=tk.RIGHT)

    def _build_action_buttons(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 8))

        btn_font = ("Microsoft YaHei UI", 11, "bold")
        btn_padx = 20
        btn_pady = 8

        self.convert_btn = tk.Button(
            frame, text="", command=self._on_start_click,
            font=btn_font, fg=BTN_START_TEXT, bg=BTN_START_NORMAL,
            activeforeground=BTN_START_TEXT, activebackground=BTN_START_ACTIVE,
            disabledforeground=BTN_START_TEXT, bd=0, relief=tk.FLAT,
            cursor="hand2", padx=btn_padx, pady=btn_pady,
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.convert_btn.bind("<Enter>", lambda e: self._btn_hover(self.convert_btn, BTN_START_NORMAL, BTN_START_HOVER, BTN_START_DISABLED))
        self.convert_btn.bind("<Leave>", lambda e: self._btn_hover(self.convert_btn, BTN_START_HOVER, BTN_START_NORMAL, BTN_START_DISABLED))
        self.convert_btn.bind("<ButtonPress-1>", lambda e: self._btn_press(self.convert_btn, BTN_START_ACTIVE, BTN_START_DISABLED))
        self.convert_btn.bind("<ButtonRelease-1>", lambda e: self._btn_release(self.convert_btn, BTN_START_HOVER, BTN_START_NORMAL, BTN_START_DISABLED))

        self.stop_btn = tk.Button(
            frame, text="", command=self._stop_conversion,
            font=btn_font, fg=BTN_START_TEXT, bg=BTN_STOP_NORMAL,
            activeforeground=BTN_START_TEXT, activebackground=BTN_STOP_ACTIVE,
            disabledforeground="#FFFFFF", bd=0, relief=tk.FLAT,
            cursor="hand2", padx=btn_padx, pady=btn_pady, state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.stop_btn.bind("<Enter>", lambda e: self._btn_hover(self.stop_btn, BTN_STOP_NORMAL, BTN_STOP_HOVER, BTN_STOP_DISABLED))
        self.stop_btn.bind("<Leave>", lambda e: self._btn_hover(self.stop_btn, BTN_STOP_HOVER, BTN_STOP_NORMAL, BTN_STOP_DISABLED))
        self.stop_btn.bind("<ButtonPress-1>", lambda e: self._btn_press(self.stop_btn, BTN_STOP_ACTIVE, BTN_STOP_DISABLED))
        self.stop_btn.bind("<ButtonRelease-1>", lambda e: self._btn_release(self.stop_btn, BTN_STOP_HOVER, BTN_STOP_NORMAL, BTN_STOP_DISABLED))

        self.browse_btn = tk.Button(
            frame, text="", command=self._browse_files,
            font=("Microsoft YaHei UI", 10), fg=BTN_START_TEXT, bg=BTN_BROWSE_NORMAL,
            activeforeground=BTN_START_TEXT, activebackground=BTN_BROWSE_ACTIVE,
            bd=0, relief=tk.FLAT, cursor="hand2", padx=14, pady=btn_pady,
        )
        self.browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.browse_btn.bind("<Enter>", lambda e: self._btn_hover(self.browse_btn, BTN_BROWSE_NORMAL, BTN_BROWSE_HOVER, None))
        self.browse_btn.bind("<Leave>", lambda e: self._btn_hover(self.browse_btn, BTN_BROWSE_HOVER, BTN_BROWSE_NORMAL, None))
        self.browse_btn.bind("<ButtonPress-1>", lambda e: self._btn_press(self.browse_btn, BTN_BROWSE_ACTIVE, None))
        self.browse_btn.bind("<ButtonRelease-1>", lambda e: self._btn_release(self.browse_btn, BTN_BROWSE_HOVER, BTN_BROWSE_NORMAL, None))

        self.detail_text = tk.Text(
            parent, height=3, font=("Consolas", 9),
            bg=COLORS["surface"], fg=COLORS["text"],
            relief=tk.FLAT, highlightthickness=1,
            highlightcolor=COLORS["border"], wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.detail_text.pack(fill=tk.X, pady=(0, 4))

    def _btn_hover(self, btn, normal_color, hover_color, disabled_color):
        if str(btn.cget("state")) == "disabled":
            return
        btn.configure(bg=hover_color)

    def _btn_press(self, btn, active_color, disabled_color):
        if str(btn.cget("state")) == "disabled":
            return
        btn.configure(bg=active_color)

    def _btn_release(self, btn, hover_color, normal_color, disabled_color):
        if str(btn.cget("state")) == "disabled":
            return
        btn.configure(bg=hover_color)

    def _on_start_click(self):
        self.convert_btn.configure(bg=BTN_START_ACTIVE)
        self.root.after(120, lambda: self.convert_btn.configure(bg=BTN_START_NORMAL))
        self._start_conversion()

    def _set_start_button_state(self, enabled: bool):
        if enabled:
            self.convert_btn.configure(state=tk.NORMAL, bg=BTN_START_NORMAL)
        else:
            self.convert_btn.configure(state=tk.DISABLED, bg=BTN_START_DISABLED)

    def _set_stop_button_state(self, enabled: bool):
        if enabled:
            self.stop_btn.configure(state=tk.NORMAL, bg=BTN_STOP_NORMAL)
        else:
            self.stop_btn.configure(state=tk.DISABLED, bg=BTN_STOP_DISABLED)

    def _build_history_area(self, parent):
        self.history_frame = ttk.LabelFrame(parent, text="", padding=8)
        self.history_frame.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(self.history_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("time", "source", "status", "duration", "predicted", "error")
        self.history_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=4,
        )
        self.history_tree.heading("time", text="")
        self.history_tree.heading("source", text="")
        self.history_tree.heading("status", text="")
        self.history_tree.heading("duration", text="")
        self.history_tree.heading("predicted", text="")
        self.history_tree.heading("error", text="")

        self.history_tree.column("time", width=130, minwidth=100)
        self.history_tree.column("source", width=180, minwidth=120)
        self.history_tree.column("status", width=60, minwidth=50)
        self.history_tree.column("duration", width=70, minwidth=50)
        self.history_tree.column("predicted", width=70, minwidth=50)
        self.history_tree.column("error", width=160, minwidth=80)

        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self.history_frame)
        btn_frame.pack(fill=tk.X, pady=(6, 0))

        self.refresh_history_btn = ttk.Button(btn_frame, text="", command=self._refresh_history)
        self.refresh_history_btn.pack(side=tk.LEFT)
        self.clear_history_btn = ttk.Button(btn_frame, text="", command=self._clear_history)
        self.clear_history_btn.pack(side=tk.LEFT, padx=(8, 0))

    def _setup_dnd(self):
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
        self.drop_frame.dnd_bind("<<DragEnter>>", self._on_drag_enter)
        self.drop_frame.dnd_bind("<<DragLeave>>", self._on_drag_leave)

    def _on_drop(self, event):
        self.drop_frame.configure(bg=COLORS["drop_zone"])
        self.drop_label.configure(background=COLORS["drop_zone"])
        self.drop_icon.configure(background=COLORS["drop_zone"])
        self.drop_sub.configure(background=COLORS["drop_zone"])

        raw = event.data
        paths = self._parse_dropped_files(raw)
        added = 0
        for p in paths:
            p = p.strip()
            if not p:
                continue
            norm = normalize_path(p)
            if os.path.isdir(norm):
                for f in os.listdir(norm):
                    full = os.path.join(norm, f)
                    if os.path.isfile(full):
                        valid, _ = validate_file(full)
                        if valid and full not in self._file_list:
                            self._file_list.append(full)
                            added += 1
            elif os.path.isfile(norm):
                valid, _ = validate_file(norm)
                if valid and norm not in self._file_list:
                    self._file_list.append(norm)
                    added += 1
                elif not valid:
                    _, err = validate_file(norm)
                    self._append_detail(t("skip_invalid", path=norm, reason=err))
            else:
                self._append_detail(t("path_not_exist", path=norm))

        self._refresh_file_list()
        if added > 0:
            self._update_status_label()
            self._append_detail(t("added_files", count=added))

    def _on_drag_enter(self, event):
        self.drop_frame.configure(bg=COLORS["drop_zone_active"])
        self.drop_label.configure(background=COLORS["drop_zone_active"])
        self.drop_icon.configure(background=COLORS["drop_zone_active"])
        self.drop_sub.configure(background=COLORS["drop_zone_active"])

    def _on_drag_leave(self, event):
        self.drop_frame.configure(bg=COLORS["drop_zone"])
        self.drop_label.configure(background=COLORS["drop_zone"])
        self.drop_icon.configure(background=COLORS["drop_zone"])
        self.drop_sub.configure(background=COLORS["drop_zone"])

    @staticmethod
    def _parse_dropped_files(raw: str) -> List[str]:
        paths = []
        if not raw:
            return paths
        if raw.startswith("{"):
            import re
            matches = re.findall(r'\{([^}]+)\}', raw)
            paths.extend(matches)
            remaining = re.sub(r'\{[^}]+\}', '', raw).strip()
            if remaining:
                paths.extend(remaining.split())
        else:
            paths = raw.split()
        return paths

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title=t("browse_title"),
            filetypes=[
                (t("filter_all_supported"), "*.pdf *.docx *.pptx *.xlsx *.xls *.html *.htm *.csv *.json *.xml *.txt *.md *.png *.jpg *.jpeg *.gif *.bmp *.mp3 *.wav *.zip"),
                (t("filter_pdf"), "*.pdf"),
                (t("filter_word"), "*.docx"),
                (t("filter_ppt"), "*.pptx"),
                (t("filter_excel"), "*.xlsx *.xls"),
                (t("filter_html"), "*.html *.htm"),
                (t("filter_text"), "*.txt *.md *.csv *.json *.xml"),
                (t("filter_image"), "*.png *.jpg *.jpeg *.gif *.bmp"),
                (t("filter_audio"), "*.mp3 *.wav"),
                (t("filter_all"), "*.*"),
            ],
        )
        added = 0
        for f in files:
            if f not in self._file_list:
                self._file_list.append(f)
                added += 1
        if added > 0:
            self._refresh_file_list()
            self._update_status_label()
            self._append_detail(t("added_files", count=added))

    def _add_path(self):
        raw = self.path_var.get().strip()
        if not raw:
            return
        paths = [p.strip() for p in raw.split(";") if p.strip()]
        added = 0
        for p in paths:
            norm = normalize_path(p)
            valid, err = validate_file(norm)
            if valid and norm not in self._file_list:
                self._file_list.append(norm)
                added += 1
            elif not valid:
                self._append_detail(t("invalid_file", path=norm, reason=err))
            elif norm in self._file_list:
                self._append_detail(t("duplicate_file", path=norm))
        if added > 0:
            self._refresh_file_list()
            self._update_status_label()
            self._append_detail(t("added_files", count=added))
        self.path_var.set("")

    def _remove_selected(self):
        selection = self.file_tree.selection()
        if not selection:
            return
        paths_to_remove = set()
        for item_id in selection:
            values = self.file_tree.item(item_id, "values")
            path_val = values[4]
            paths_to_remove.add(path_val)
        self._file_list = [f for f in self._file_list if f not in paths_to_remove]
        self._refresh_file_list()

    def _clear_list(self):
        if not self._file_list:
            return
        if messagebox.askyesno(t("confirm_title"), t("confirm_clear_list")):
            self._file_list.clear()
            self._file_meta.clear()
            self._sort_column = "index"
            self._sort_direction = SORT_NONE
            self._refresh_file_list()
            self._update_status_label()
            self._append_detail(t("list_cleared"))

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        if size_bytes < 0:
            return "0 B"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                if unit == "B":
                    return f"{size_bytes} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def _on_column_click(self, column: str):
        if column not in SORTABLE_COLUMNS:
            return
        if self._sort_column == column:
            if self._sort_direction == SORT_ASC:
                self._sort_direction = SORT_DESC
            elif self._sort_direction == SORT_DESC:
                self._sort_column = "index"
                self._sort_direction = SORT_NONE
            else:
                self._sort_direction = SORT_ASC
        else:
            self._sort_column = column
            self._sort_direction = SORT_ASC
        self._apply_sort()
        self._update_heading_arrows()
        self._render_tree()

    def _apply_sort(self):
        if self._sort_direction == SORT_NONE or self._sort_column == "index":
            return
        reverse = self._sort_direction == SORT_DESC
        if self._sort_column == "filename":
            self._file_list.sort(key=lambda f: os.path.basename(f).lower(), reverse=reverse)
        elif self._sort_column == "size":
            self._file_list.sort(key=lambda f: self._file_meta.get(f, {}).get("size", 0), reverse=reverse)
        elif self._sort_column == "predicted":
            self._file_list.sort(key=lambda f: self._file_meta.get(f, {}).get("pred_seconds", 0.0), reverse=reverse)

    def _update_heading_arrows(self):
        base_titles = {
            "filename": t("col_filename"),
            "size": t("col_size"),
            "predicted": t("col_predicted"),
        }
        for col, base in base_titles.items():
            if col == self._sort_column and self._sort_direction != SORT_NONE:
                arrow = SORT_ASC if self._sort_direction == SORT_ASC else SORT_DESC
                title = base + arrow
            else:
                title = base
            self.file_tree.heading(col, text=title)

    def _refresh_file_list(self):
        self._file_meta.clear()
        total_size = 0
        for f in self._file_list:
            try:
                size = os.path.getsize(f)
            except OSError:
                size = 0
            total_size += size
            pred = self.predictor.predict(f, file_size=size)
            self._file_meta[f] = {
                "size": size,
                "pred_seconds": pred.predicted_seconds,
                "pred_display": pred.predicted_display,
            }
        self._apply_sort()
        self._update_heading_arrows()
        self._render_tree()
        self._refresh_file_list_labels()
        self._update_prediction_panel()

    def _refresh_file_list_labels(self):
        self.count_label.configure(text=t("count_files", count=len(self._file_list)))
        total_size = sum(m.get("size", 0) for m in self._file_meta.values())
        self.total_size_label.configure(text=t("total_size", size=self._fmt_size(total_size)))

    def _render_tree(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        for i, f in enumerate(self._file_list):
            meta = self._file_meta.get(f, {})
            size_str = self._fmt_size(meta.get("size", 0))
            pred_str = meta.get("pred_display", "--")
            basename = os.path.basename(f)
            self.file_tree.insert("", tk.END, values=(i + 1, basename, size_str, pred_str, f))

    def _update_prediction_panel(self):
        if not self._file_list:
            self.pred_total_label.configure(text=t("pred_total_none"))
            self.pred_range_label.configure(text="")
            self.pred_confidence_label.configure(text="")
            self.pred_detail_label.configure(text="")
            return

        total_pred, total_lower, total_upper = self.predictor.predict_batch(self._file_list)

        self.pred_total_label.configure(
            text=t("pred_total", time=PredictionResult._format_time(total_pred))
        )

        lower_fmt = PredictionResult._format_time(total_lower)
        upper_fmt = PredictionResult._format_time(total_upper)
        self.pred_range_label.configure(text=t("pred_range", lower=lower_fmt, upper=upper_fmt))

        confidences = []
        cat_counts = {}
        for f in self._file_list:
            pred = self.predictor.predict(f)
            confidences.append(pred.confidence)
            cat = pred.category_name
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        if "low" in confidences:
            conf_text = t("confidence_low")
            conf_color = COLORS["error"]
        elif "medium" in confidences:
            conf_text = t("confidence_medium")
            conf_color = COLORS["warning"]
        else:
            conf_text = t("confidence_high")
            conf_color = COLORS["success"]

        self.pred_confidence_label.configure(text=conf_text, foreground=conf_color)

        detail_parts = [f"{name}×{count}" for name, count in cat_counts.items()]
        self.pred_detail_label.configure(text=t("file_composition", parts=", ".join(detail_parts)))

    def _update_status_label(self):
        status = t("status_ready")
        style = "Status.TLabel"
        color = COLORS["text_secondary"]
        self.status_label.configure(text=status, style=style, foreground=color)

    def _set_status(self, status_key: str):
        style_map = {
            "status_ready": ("Status.TLabel", COLORS["text_secondary"]),
            "status_converting": ("Warning.TLabel", COLORS["warning"]),
            "status_success": ("Success.TLabel", COLORS["success"]),
            "status_failed": ("Error.TLabel", COLORS["error"]),
        }
        style, color = style_map.get(status_key, ("Status.TLabel", COLORS["text_secondary"]))
        self.status_label.configure(text=t(status_key), style=style, foreground=color)

    def _append_detail(self, text: str):
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.insert(tk.END, text + "\n")
        self.detail_text.see(tk.END)
        self.detail_text.configure(state=tk.DISABLED)

    def _clear_detail(self):
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.configure(state=tk.DISABLED)

    def _start_timer(self):
        self._timer_start = time.monotonic()
        self._tick_timer()

    def _tick_timer(self):
        if self._timer_start is None:
            return
        elapsed = time.monotonic() - self._timer_start
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        self.timer_label.configure(text=f"⏱ {mins:02d}:{secs:02d}")
        self._timer_id = self.root.after(500, self._tick_timer)

    def _stop_timer(self):
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        if self._timer_start is not None:
            elapsed = time.monotonic() - self._timer_start
            mins = int(elapsed) // 60
            secs = int(elapsed) % 60
            self.timer_label.configure(text=f"⏱ {mins:02d}:{secs:02d}")
            self._timer_start = None

    def _reset_timer(self):
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._timer_start = None
        self.timer_label.configure(text="⏱ 00:00")

    def _start_conversion(self):
        if self._converting:
            return
        if not self._file_list:
            messagebox.showwarning(t("warning_title"), t("warning_no_files"))
            return

        total_pred, total_lower, total_upper = self.predictor.predict_batch(self._file_list)
        pred_display = PredictionResult._format_time(total_pred)
        lower_display = PredictionResult._format_time(total_lower)
        upper_display = PredictionResult._format_time(total_upper)
        msg = t("confirm_convert_msg",
                count=len(self._file_list),
                pred=pred_display, lower=lower_display, upper=upper_display)
        if not messagebox.askyesno(t("confirm_convert_title"), msg):
            return

        self._converting = True
        self._stop_requested = False
        self._set_start_button_state(False)
        self._set_stop_button_state(True)
        self._set_status("status_converting")
        self._clear_detail()
        self._reset_timer()
        self._start_timer()

        self._append_detail(t("pred_total_detail", pred=pred_display, lower=lower_display, upper=upper_display))

        thread = threading.Thread(target=self._conversion_worker, daemon=True)
        thread.start()

    def _stop_conversion(self):
        if self._converting:
            self._stop_requested = True
            self._append_detail(t("stopping"))

    def _conversion_worker(self):
        total = len(self._file_list)
        success_count = 0
        fail_count = 0

        for i, file_path in enumerate(self._file_list):
            if self._stop_requested:
                self.root.after(0, self._append_detail, t("stopped"))
                break

            pred = self.predictor.predict(file_path)

            self.root.after(0, self._set_status, "status_converting")
            self.root.after(
                0, self._append_detail,
                t("converting_item", current=i + 1, total=total,
                  name=os.path.basename(file_path), pred=pred.predicted_display),
            )

            result = self.engine.convert_file(file_path)

            if result.success:
                self.predictor.record_actual(file_path, result.file_size, result.duration)
                success_count += 1

                error_pct = ""
                if pred.predicted_seconds > 0:
                    err_rate = abs(result.duration - pred.predicted_seconds) / pred.predicted_seconds * 100
                    error_pct = t("error_pct", pct=f"{err_rate:.1f}")

                msg = t("convert_success",
                        current=i + 1, total=total,
                        name=os.path.basename(file_path),
                        output=result.output_path,
                        actual=f"{result.duration:.2f}",
                        pred=pred.predicted_display, error=error_pct)
                self.root.after(0, self._append_detail, msg)
            else:
                fail_count += 1
                msg = t("convert_failed",
                        current=i + 1, total=total,
                        name=os.path.basename(file_path), error=result.error)
                self.root.after(0, self._append_detail, msg)

        self._converting = False

        def finalize():
            self._stop_timer()
            self._set_start_button_state(True)
            self._set_stop_button_state(False)

            if fail_count == 0 and success_count > 0:
                self._set_status("status_success")
                self._append_detail(t("all_done", count=success_count))
            elif success_count > 0 and fail_count > 0:
                self._set_status("status_failed")
                self._append_detail(t("partial_done", success=success_count, fail=fail_count))
            elif fail_count > 0:
                self._set_status("status_failed")
                self._append_detail(t("all_failed", count=fail_count))

            self._refresh_history()
            self._refresh_file_list()

        self.root.after(0, finalize)

    def _refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        records = self.engine.get_history()
        for rec in reversed(records[-100:]):
            ts = rec.timestamp[:19].replace("T", " ") if rec.timestamp else ""
            src = os.path.basename(rec.source_path) if rec.source_path else ""
            if rec.status == "success":
                status_text = t("status_success_short")
            elif rec.status == "failed":
                status_text = t("status_failed_short")
            elif rec.status == "empty":
                status_text = t("status_empty_short")
            else:
                status_text = rec.status
            dur = f"{rec.duration:.2f}s" if rec.duration else ""

            pred = self.predictor.predict(rec.source_path, file_size=rec.file_size)
            pred_str = pred.predicted_display

            err = (rec.error[:60] + "...") if rec.error and len(rec.error) > 60 else (rec.error or "")
            self.history_tree.insert("", tk.END, values=(ts, src, status_text, dur, pred_str, err))

    def _clear_history(self):
        if messagebox.askyesno(t("confirm_title"), t("confirm_clear_history")):
            self.engine.clear_history()
            self._refresh_history()
            self._append_detail(t("history_cleared"))
