import os
import tkinter as tk
from src.components.main_window import MainWindow
from src.config import WINDOW_TITLE, BG_BLACK


if __name__ == "__main__":
    root = tk.Tk()
    root.title(WINDOW_TITLE)

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    root.resizable(False, False)
    root.configure(bg=BG_BLACK)

    app = MainWindow(root)

    root.mainloop()
