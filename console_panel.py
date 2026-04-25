import sys
import io
import time
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable

from i18n import t


class QueueStream(io.TextIOBase):
    def __init__(self, callback: Callable[[str, str], None], stream_type: str):
        self._callback = callback
        self._stream_type = stream_type
        self._lock = threading.Lock()
        self._original = sys.__stdout__ if stream_type == "stdout" else sys.__stderr__

    def write(self, text: str) -> int:
        if not text:
            return 0
        with self._lock:
            self._callback(text, self._stream_type)
        if self._original:
            try:
                self._original.write(text)
                self._original.flush()
            except Exception:
                pass
        return len(text)

    def flush(self):
        if self._original:
            try:
                self._original.flush()
            except Exception:
                pass

    def fileno(self):
        if self._original:
            return self._original.fileno()
        raise io.UnsupportedOperation("fileno")


class ConsolePanel(ttk.Frame):
    TAG_STDOUT = "stdout"
    TAG_STDERR = "stderr"
    TAG_INFO = "info"
    TAG_WARNING = "warning"
    TAG_ERROR = "error"
    TAG_DEBUG = "debug"

    MAX_LINES = 2000
    TRIM_LINES = 500

    def __init__(self, parent, app_root: tk.Tk, **kwargs):
        super().__init__(parent, **kwargs)
        self.app_root = app_root
        self._expanded = False
        self._auto_scroll = True
        self._pending_writes = []
        self._write_lock = threading.Lock()
        self._flush_scheduled = False
        self._flush_interval = 50

        self._setup_styles()
        self._build_ui()
        self._setup_redirection()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure("Console.TFrame", background="#1E1E1E")

    def _build_ui(self):
        self.configure(style="Console.TFrame", padding=0)

        self._header = tk.Frame(self, bg="#2D2D2D", height=28)
        self._header.pack(fill=tk.X, side=tk.TOP)
        self._header.pack_propagate(False)

        self._toggle_btn = tk.Label(
            self._header, text=f"▶ {t('console_title')}", bg="#2D2D2D", fg="#CCCCCC",
            font=("Microsoft YaHei UI", 9), cursor="hand2", anchor=tk.W,
        )
        self._toggle_btn.pack(side=tk.LEFT, padx=(8, 0), fill=tk.Y)
        self._toggle_btn.bind("<Button-1>", self._toggle_expand)

        self._auto_scroll_var = tk.BooleanVar(value=True)
        self._auto_scroll_cb = tk.Checkbutton(
            self._header, text=t("console_auto_scroll"), variable=self._auto_scroll_var,
            bg="#2D2D2D", fg="#AAAAAA", selectcolor="#2D2D2D",
            activebackground="#2D2D2D", activeforeground="#CCCCCC",
            font=("Microsoft YaHei UI", 8), command=self._on_auto_scroll_toggle,
        )
        self._auto_scroll_cb.pack(side=tk.LEFT, padx=(12, 0))

        self._clear_btn = tk.Label(
            self._header, text=t("console_clear"), bg="#2D2D2D", fg="#888888",
            font=("Microsoft YaHei UI", 8), cursor="hand2",
        )
        self._clear_btn.pack(side=tk.RIGHT, padx=(8, 0), fill=tk.Y)
        self._clear_btn.bind("<Button-1>", lambda e: self._clear_console())

        self._copy_btn = tk.Label(
            self._header, text=t("console_copy"), bg="#2D2D2D", fg="#888888",
            font=("Microsoft YaHei UI", 8), cursor="hand2",
        )
        self._copy_btn.pack(side=tk.RIGHT, padx=(8, 0), fill=tk.Y)
        self._copy_btn.bind("<Button-1>", lambda e: self._copy_console())

        self._body = tk.Frame(self, bg="#1E1E1E")

        self._text = tk.Text(
            self._body, bg="#1E1E1E", fg="#D4D4D4",
            font=("Consolas", 9), wrap=tk.WORD,
            relief=tk.FLAT, bd=0, padx=8, pady=4,
            insertbackground="#D4D4D4", cursor="arrow",
            state=tk.DISABLED, highlightthickness=0,
            height=8,
        )

        self._scrollbar = ttk.Scrollbar(
            self._body, orient=tk.VERTICAL, command=self._text.yview,
        )
        self._text.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._text.tag_configure(self.TAG_STDOUT, foreground="#D4D4D4")
        self._text.tag_configure(self.TAG_STDERR, foreground="#F44747")
        self._text.tag_configure(self.TAG_INFO, foreground="#4EC9B0")
        self._text.tag_configure(self.TAG_WARNING, foreground="#DCDCAA")
        self._text.tag_configure(self.TAG_ERROR, foreground="#F44747")
        self._text.tag_configure(self.TAG_DEBUG, foreground="#6A9955")

        self._text.bind("<Enter>", lambda e: self._text.configure(cursor="ibeam"))
        self._text.bind("<Leave>", lambda e: self._text.configure(cursor="arrow"))

    def _toggle_expand(self, event=None):
        if self._expanded:
            self._body.pack_forget()
            self._toggle_btn.configure(text=f"▶ {t('console_title')}")
            self._expanded = False
        else:
            self._body.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
            self._toggle_btn.configure(text=f"▼ {t('console_title')}")
            self._expanded = True
            if self._auto_scroll:
                self._scroll_to_end()

    def _on_auto_scroll_toggle(self):
        self._auto_scroll = self._auto_scroll_var.get()

    def _clear_console(self):
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)

    def _copy_console(self):
        content = self._text.get("1.0", tk.END).strip()
        if content:
            self.app_root.clipboard_clear()
            self.app_root.clipboard_append(content)

    def _scroll_to_end(self):
        try:
            self._text.see(tk.END)
        except Exception:
            pass

    def _setup_redirection(self):
        self._stdout_stream = QueueStream(self._enqueue_write, "stdout")
        self._stderr_stream = QueueStream(self._enqueue_write, "stderr")
        sys.stdout = self._stdout_stream
        sys.stderr = self._stderr_stream

    def _enqueue_write(self, text: str, stream_type: str):
        with self._write_lock:
            self._pending_writes.append((text, stream_type))
        if not self._flush_scheduled:
            self._flush_scheduled = True
            try:
                self.app_root.after(self._flush_interval, self._flush_pending)
            except Exception:
                self._flush_scheduled = False

    def _flush_pending(self):
        self._flush_scheduled = False
        with self._write_lock:
            writes = self._pending_writes[:]
            self._pending_writes.clear()

        if not writes:
            return

        tag_map = {
            "debug": self.TAG_DEBUG,
            "info": self.TAG_INFO,
            "warning": self.TAG_WARNING,
            "error": self.TAG_ERROR,
            "critical": self.TAG_ERROR,
            "stdout": self.TAG_STDOUT,
            "stderr": self.TAG_STDERR,
        }

        self._text.configure(state=tk.NORMAL)
        for text, stream_type in writes:
            tag = tag_map.get(stream_type, self.TAG_STDOUT)
            self._text.insert(tk.END, text, (tag,))

        line_count = int(self._text.index("end-1c").split(".")[0])
        if line_count > self.MAX_LINES:
            trim_to = self.MAX_LINES - self.TRIM_LINES
            self._text.delete("1.0", f"{trim_to}.0")

        self._text.configure(state=tk.DISABLED)

        if self._auto_scroll:
            self._scroll_to_end()

    def write_log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}\n"

        with self._write_lock:
            self._pending_writes.append((line, level.lower()))

        if not self._flush_scheduled:
            self._flush_scheduled = True
            try:
                self.app_root.after(self._flush_interval, self._flush_pending)
            except Exception:
                self._flush_scheduled = False

    def write(self, text: str):
        if not text or not text.strip():
            return
        level = "INFO"
        stripped = text.strip()
        if stripped.startswith("[DEBUG]"):
            level = "DEBUG"
        elif stripped.startswith("[WARNING]"):
            level = "WARNING"
        elif stripped.startswith("[ERROR]") or stripped.startswith("[CRITICAL]"):
            level = "ERROR"
        self.write_log(stripped, level)

    def flush(self):
        pass

    def restore_streams(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def destroy(self):
        self.restore_streams()
        super().destroy()
