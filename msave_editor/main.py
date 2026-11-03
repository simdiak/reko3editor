"""
《三国志英杰传》存档编辑器 (MSAVE Editor) 启动入口
运行命令:
    python3 msave_editor/main.py
或者指定存档文件启动:
    python3 msave_editor/main.py ./msave_editor/samples/MSAVE0.R3S
"""

import sys
import os
import tkinter as tk

# 确保包能够被正确导入
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from msave_editor.ui import MSaveEditorApp


def main():
    root = tk.Tk()
    app = MSaveEditorApp(root)

    # 如果命令行传入了具体存档文件路径，直接打开
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app.load_save_file(sys.argv[1])

    root.mainloop()


if __name__ == '__main__':
    main()

