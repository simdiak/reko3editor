"""
《三国志英杰传》游戏程序修改器 (Main.exe Patcher) 启动入口
运行命令:
    python3 prog_editor/main.py
或者指定游戏根目录直接打开:
    python3 prog_editor/main.py ./backend/reko3
"""

import sys
import os
import tkinter as tk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from prog_editor.ui import ProgEditorApp


def main():
    root = tk.Tk()
    app = ProgEditorApp(root)

    # 如果命令行传入了游戏目录参数，直接尝试载入
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        app._load_game_directory(sys.argv[1])

    root.mainloop()


if __name__ == '__main__':
    main()

