import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger_config import setup_logging

_TKDND_AVAILABLE = False
TkinterDnD = None
try:
    from tkinterdnd2 import TkinterDnD as _TkinterDnD
    TkinterDnD = _TkinterDnD
    _TKDND_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    import tkinter as tk
    TkinterDnD = tk
    logger = logging.getLogger("markitdown_gui")
    logger.warning(
        "tkinterdnd2 不可用 (%s)，将回退到标准 Tkinter（拖拽功能不可用）。"
        "如需拖拽功能，请安装系统级 tkdnd 库。Linux: apt-get install tkdnd",
        e,
    )


def main():
    setup_logging()

    root = (TkinterDnD.Tk() if _TKDND_AVAILABLE else TkinterDnD.Tk())
    app = MarkItDownApp(root)

    root.protocol("WM_DELETE_WINDOW", _on_close(root, app))
    root.mainloop()


def _on_close(root, app):
    def handler():
        try:
            if hasattr(app, 'console_panel'):
                app.console_panel.restore_streams()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
    return handler


if __name__ == "__main__":
    from gui import MarkItDownApp
    main()
