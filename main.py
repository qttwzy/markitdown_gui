import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger_config import setup_logging
from gui import MarkItDownApp

from tkinterdnd2 import TkinterDnD


def main():
    setup_logging()

    root = TkinterDnD.Tk()
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
    main()
