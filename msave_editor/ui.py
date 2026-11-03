"""
《三国志英杰传》存档编辑器 - Tkinter 图形界面模块
支持左右分栏布局、武将属性与8格道具编辑、金钱修改与回写保存
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, List

from msave_editor.constants import (
    JUNTUAN_MAP,
    BINGZHONG_LIST,
    DAOJU_LIST
)
from msave_editor.parser import SaveFile, Avatar


class MSaveEditorApp:
    """主窗口应用程序"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("《三国志英杰传》存档编辑器 - MSAVE Editor")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 640)

        self.current_save: Optional[SaveFile] = None
        self.selected_avatar: Optional[Avatar] = None
        self._updating_form = False  # 防止表单赋值时触发循环修改事件

        self.sort_column = "index"
        self.sort_descending = False

        self._setup_style()
        self._build_ui()
        self._load_default_sample()
        # 默认将武将属性侧栏宽度设置为原始窗口宽度的 1/3 (左侧占 2/3)
        self.root.after(50, self._set_default_sash_position)

    def _setup_style(self):
        """配置 ttk 控件样式"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        self.font_main = ('Sans', 10)
        self.font_bold = ('Sans', 10, 'bold')
        self.font_title = ('Sans', 12, 'bold')
        self.font_header = ('Sans', 11, 'bold')

        style.configure('Treeview', font=self.font_main, rowheight=26)
        style.configure('Treeview.Heading', font=self.font_bold)
        style.configure('TLabel', font=self.font_main)
        style.configure('TButton', font=self.font_main)
        style.configure('Save.TButton', font=self.font_bold)

    def _build_ui(self):
        """构建整体 UI 布局"""
        # ================= 1. 顶部操作工具栏 =================
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X, side=tk.TOP)

        btn_open = ttk.Button(
            top_frame, text="📂 打开存档...", command=self._on_open_file
        )
        btn_open.pack(side=tk.LEFT, padx=(0, 6))

        # 样例快速加载下拉框
        ttk.Label(top_frame, text="样例:").pack(side=tk.LEFT, padx=(4, 2))
        self.sample_combo = ttk.Combobox(
            top_frame,
            values=["MSAVE0.R3S", "MSAVE1.R3S", "MSAVE2.R3S", "MSAVE3.R3S", "MSAVE4.R3S"],
            state="readonly",
            width=12
        )
        self.sample_combo.set("MSAVE0.R3S")
        self.sample_combo.pack(side=tk.LEFT, padx=(0, 4))
        self.sample_combo.bind("<<ComboboxSelected>>", self._on_select_sample)

        btn_load_sample = ttk.Button(top_frame, text="载入", command=self._on_load_sample_btn, width=5)
        btn_load_sample.pack(side=tk.LEFT, padx=(0, 15))

        # 保存按钮组
        self.btn_save = ttk.Button(
            top_frame, text="💾 保存修改", style='Save.TButton', command=self._on_save
        )
        self.btn_save.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_save_as = ttk.Button(
            top_frame, text="💾 另存为...", command=self._on_save_as
        )
        self.btn_save_as.pack(side=tk.LEFT, padx=(0, 15))

        self.lbl_filepath = ttk.Label(top_frame, text="未打开文件", foreground="#666666")
        self.lbl_filepath.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ================= 2. 存档概览与金钱编辑栏 =================
        self.info_frame = ttk.LabelFrame(self.root, text=" 存档信息与金钱修改 ", padding=(12, 8))
        self.info_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        info_sub = ttk.Frame(self.info_frame)
        info_sub.pack(fill=tk.X)

        # 章节名
        self.lbl_chapter = ttk.Label(
            info_sub, text="章节: 【尚未载入】", font=self.font_header, foreground="#2C3E50"
        )
        self.lbl_chapter.pack(side=tk.LEFT, padx=(0, 30))

        # 金钱输入与修改区域
        ttk.Label(info_sub, text="💰 军团金钱:", font=self.font_bold).pack(side=tk.LEFT, padx=(0, 4))
        self.money_var = tk.StringVar(value="0")
        self.money_spin = ttk.Spinbox(
            info_sub,
            from_=0,
            to=10000,
            textvariable=self.money_var,
            width=8,
            font=self.font_bold
        )
        self.money_spin.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(info_sub, text="(上限 10000)").pack(side=tk.LEFT, padx=(0, 6))

        btn_max_money = ttk.Button(
            info_sub, text="满钱(10000)", command=lambda: self.money_var.set("10000"), width=11
        )
        btn_max_money.pack(side=tk.LEFT, padx=(0, 30))

        # 武将总览
        self.lbl_avatar_summary = ttk.Label(
            info_sub, text="武将统计: 共 0 人", font=self.font_main
        )
        self.lbl_avatar_summary.pack(side=tk.LEFT)

        # ================= 3. 中间左右分栏工作区 =================
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        # --- 左侧：列表与过滤栏 (占 2/3) ---
        left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(left_frame, weight=2)

        # 过滤栏
        filter_frame = ttk.Frame(left_frame, padding=(0, 0, 0, 6))
        filter_frame.pack(fill=tk.X)

        ttk.Label(filter_frame, text="军团:").pack(side=tk.LEFT, padx=(0, 2))
        juntuan_options = ["劉備", "全部军团"] + [
            name for name in JUNTUAN_MAP.values() if name != "劉備"
        ]
        self.juntuan_var = tk.StringVar(value="劉備")
        self.juntuan_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.juntuan_var,
            values=juntuan_options,
            state="readonly",
            width=9
        )
        self.juntuan_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.juntuan_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())

        ttk.Label(filter_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 2))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=14)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_var.trace_add("write", lambda *args: self._refresh_table())

        self.has_items_var = tk.BooleanVar(value=False)
        chk_items = ttk.Checkbutton(
            filter_frame,
            text="有装备",
            variable=self.has_items_var,
            command=self._refresh_table
        )
        chk_items.pack(side=tk.LEFT, padx=(0, 6))

        btn_reset = ttk.Button(filter_frame, text="重置", command=self._reset_filters, width=5)
        btn_reset.pack(side=tk.LEFT)

        self.lbl_filtered_count = ttk.Label(
            filter_frame, text="0 / 384 人", foreground="#555555"
        )
        self.lbl_filtered_count.pack(side=tk.RIGHT)

        # 表格区
        table_container = ttk.Frame(left_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = [
            ("index", "序号", 50, "center"),
            ("name", "姓名", 70, "center"),
            ("juntuan", "军团", 65, "center"),
            ("bingzhong", "兵种", 70, "center"),
            ("level", "等级", 50, "center"),
            ("exp", "经验", 50, "center"),
            ("troop", "当前兵力", 75, "e"),
            ("morale", "士气", 50, "center"),
            ("items", "携带道具", 220, "w"),
        ]

        self.tree = ttk.Treeview(
            table_container,
            columns=[col[0] for col in columns],
            show="headings",
            selectmode="browse"
        )

        for col_id, col_text, col_width, col_align in columns:
            self.tree.heading(
                col_id,
                text=col_text,
                command=lambda c=col_id: self._on_sort_column(c)
            )
            self.tree.column(col_id, width=col_width, anchor=col_align, stretch=(col_id == "items"))

        v_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # --- 右侧：武将详细信息与编辑面板 (占 1/3) ---
        self.right_container = ttk.Frame(self.main_paned, padding=(8, 0, 0, 0))
        self.main_paned.add(self.right_container, weight=1)

        # 未选中时的占位空白提示
        self.placeholder_frame = ttk.Frame(self.right_container)
        self.placeholder_frame.pack(fill=tk.BOTH, expand=True)
        self.lbl_empty_hint = ttk.Label(
            self.placeholder_frame,
            text="👈 请在左侧列表中点击选择武将进行编辑",
            font=self.font_header,
            foreground="#888888"
        )
        self.lbl_empty_hint.place(relx=0.5, rely=0.45, anchor="center")

        # 选中时的编辑面板容器
        self.editor_frame = ttk.LabelFrame(self.right_container, text=" 武将详细信息编辑 ", padding=10)

        self._build_avatar_editor_ui(self.editor_frame)

        # ================= 4. 底部状态栏 =================
        status_bar = ttk.Frame(self.root, relief="sunken", padding=(6, 3))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status = ttk.Label(
            status_bar,
            text="就绪。点击左侧武将即可在右侧实时修改军团、兵种、等级、经验与道具。",
            font=('Sans', 9)
        )
        self.lbl_status.pack(side=tk.LEFT)

        author_lbl = ttk.Label(
            status_bar,
            text="修改后请点击顶部【保存修改】按钮保存回文件",
            font=('Sans', 9),
            foreground="#006600"
        )
        author_lbl.pack(side=tk.RIGHT)

    def _build_avatar_editor_ui(self, parent: ttk.LabelFrame):
        """构建右侧武将属性与8格道具的编辑控件"""
        # 头部武将名与辅助按钮
        header_box = ttk.Frame(parent)
        header_box.pack(fill=tk.X, pady=(0, 10))

        self.lbl_editor_name = ttk.Label(
            header_box, text="【未选中】", font=self.font_title, foreground="#1B4F72"
        )
        self.lbl_editor_name.pack(side=tk.LEFT)

        btn_max_stat = ttk.Button(
            header_box, text="⚡满级满兵", command=self._quick_max_avatar, width=10
        )
        btn_max_stat.pack(side=tk.RIGHT)

        # 基本属性区域
        base_group = ttk.LabelFrame(parent, text=" 基础属性 ", padding=8)
        base_group.pack(fill=tk.X, pady=(0, 10))

        grid = ttk.Frame(base_group)
        grid.pack(fill=tk.X)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        # 所属军团
        ttk.Label(grid, text="所属军团:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.avatar_juntuan_var = tk.StringVar()
        self.avatar_juntuan_combo = ttk.Combobox(
            grid,
            textvariable=self.avatar_juntuan_var,
            values=list(JUNTUAN_MAP.values()),
            state="readonly",
            width=10
        )
        self.avatar_juntuan_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.avatar_juntuan_combo.bind("<<ComboboxSelected>>", self._on_avatar_field_change)

        # 兵种
        ttk.Label(grid, text="兵种:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.avatar_bingzhong_var = tk.StringVar()
        self.avatar_bingzhong_combo = ttk.Combobox(
            grid,
            textvariable=self.avatar_bingzhong_var,
            values=BINGZHONG_LIST,
            state="readonly",
            width=10
        )
        self.avatar_bingzhong_combo.grid(row=0, column=3, sticky="ew", padx=4, pady=4)
        self.avatar_bingzhong_combo.bind("<<ComboboxSelected>>", self._on_avatar_field_change)

        # 等级 (1~99)
        ttk.Label(grid, text="等级 (1~99):").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.avatar_level_var = tk.StringVar()
        self.avatar_level_spin = ttk.Spinbox(
            grid, from_=1, to=99, textvariable=self.avatar_level_var, width=10
        )
        self.avatar_level_spin.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.avatar_level_spin.bind("<FocusOut>", self._on_avatar_field_change)
        self.avatar_level_spin.bind("<Return>", self._on_avatar_field_change)

        # 经验 (0~99)
        ttk.Label(grid, text="经验 (0~99):").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.avatar_exp_var = tk.StringVar()
        self.avatar_exp_spin = ttk.Spinbox(
            grid, from_=0, to=99, textvariable=self.avatar_exp_var, width=10
        )
        self.avatar_exp_spin.grid(row=1, column=3, sticky="ew", padx=4, pady=4)
        self.avatar_exp_spin.bind("<FocusOut>", self._on_avatar_field_change)
        self.avatar_exp_spin.bind("<Return>", self._on_avatar_field_change)

        # 兵力
        ttk.Label(grid, text="当前兵力:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.avatar_troop_var = tk.StringVar()
        self.avatar_troop_entry = ttk.Entry(grid, textvariable=self.avatar_troop_var, width=10)
        self.avatar_troop_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        self.avatar_troop_entry.bind("<FocusOut>", self._on_avatar_field_change)
        self.avatar_troop_entry.bind("<Return>", self._on_avatar_field_change)

        # 士气 (0~100)
        ttk.Label(grid, text="士气/忠诚:").grid(row=2, column=2, sticky="w", padx=4, pady=4)
        self.avatar_morale_var = tk.StringVar()
        self.avatar_morale_spin = ttk.Spinbox(
            grid, from_=0, to=100, textvariable=self.avatar_morale_var, width=10
        )
        self.avatar_morale_spin.grid(row=2, column=3, sticky="ew", padx=4, pady=4)
        self.avatar_morale_spin.bind("<FocusOut>", self._on_avatar_field_change)
        self.avatar_morale_spin.bind("<Return>", self._on_avatar_field_change)

        # 道具区域（全 8 格完整展示）
        items_group = ttk.LabelFrame(parent, text=" 携带道具 (完整8格) ", padding=8)
        items_group.pack(fill=tk.BOTH, expand=True)

        items_top = ttk.Frame(items_group)
        items_top.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(items_top, text="可为武将选择任意道具，或选择 (空) 清空格子:").pack(side=tk.LEFT)
        btn_clear_items = ttk.Button(
            items_top, text="清空8格", command=self._clear_all_items, width=8
        )
        btn_clear_items.pack(side=tk.RIGHT)

        # 道具选项列表：第1项为 (空)，后面跟所有道具
        self.item_options = ["(空)"] + list(DAOJU_LIST)

        # 8 个下拉框排布（2 列 x 4 行，完整展示 1~8 格）
        slots_frame = ttk.Frame(items_group)
        slots_frame.pack(fill=tk.BOTH, expand=True)

        self.item_vars: List[tk.StringVar] = []
        self.item_combos: List[ttk.Combobox] = []

        for i in range(8):
            row = i % 4
            col = (i // 4) * 2

            lbl = ttk.Label(slots_frame, text=f"第 {i+1} 格:", font=self.font_bold)
            lbl.grid(row=row, column=col, sticky="w", padx=(8 if col > 0 else 2, 4), pady=5)

            var = tk.StringVar(value="(空)")
            cb = ttk.Combobox(
                slots_frame,
                textvariable=var,
                values=self.item_options,
                state="readonly",
                width=14
            )
            cb.grid(row=row, column=col+1, sticky="ew", padx=2, pady=5)
            cb.bind("<<ComboboxSelected>>", lambda e, idx=i: self._on_item_slot_change(idx))

            self.item_vars.append(var)
            self.item_combos.append(cb)

        slots_frame.grid_columnconfigure(1, weight=1)
        slots_frame.grid_columnconfigure(3, weight=1)

    # ================= 数据加载与保存逻辑 =================

    def _set_default_sash_position(self):
        """设置默认分割线位置：使右侧武将属性侧栏占原始窗口宽度的 1/3 (左侧占 2/3)"""
        try:
            self.root.update_idletasks()
            total_w = self.main_paned.winfo_width()
            if total_w > 100:
                sash_pos = int(total_w * 2 / 3)
                self.main_paned.sashpos(0, sash_pos)
        except Exception:
            pass

    def _load_default_sample(self):
        """自动载入第一个样例文件"""
        sample_path = os.path.join(
            os.path.dirname(__file__), "samples", "MSAVE0.R3S"
        )
        if os.path.exists(sample_path):
            self.load_save_file(sample_path)

    def _on_select_sample(self, event=None):
        self._on_load_sample_btn()

    def _on_load_sample_btn(self):
        name = self.sample_combo.get().strip()
        sample_path = os.path.join(
            os.path.dirname(__file__), "samples", name
        )
        if os.path.exists(sample_path):
            self.load_save_file(sample_path)
        else:
            messagebox.showwarning("提示", f"样例文件 {sample_path} 未找到！")

    def _on_open_file(self):
        filepath = filedialog.askopenfilename(
            title="选择《三国志英杰传》存档文件",
            filetypes=[
                ("英杰传存档 (*.R3S;*.r3s)", "*.R3S *.r3s"),
                ("所有文件 (*.*)", "*.*")
            ]
        )
        if filepath:
            self.load_save_file(filepath)

    def load_save_file(self, filepath: str):
        """加载存档并刷新所有控件"""
        try:
            save = SaveFile(filepath)
            self.current_save = save
        except Exception as e:
            messagebox.showerror("载入失败", f"无法解析存档文件:\n{e}")
            return

        self.selected_avatar = None
        self._show_editor_panel(False)  # 初始不选中武将，右边留空

        # 更新顶部状态
        self.lbl_filepath.configure(text=filepath, foreground="#2C3E50")
        self.lbl_chapter.configure(text=f"章节: 【{save.title}】")
        self.money_var.set(str(save.money))

        liubei_count = sum(1 for a in save.avatars if a.is_liubei_army)
        self.lbl_avatar_summary.configure(
            text=f"武将总数: 384 人 | 劉備军: {liubei_count} 人"
        )
        self.lbl_status.configure(
            text=f"成功载入存档: {save.filename} (共 {len(save.avatars)} 名武将)"
        )

        self._refresh_table()

    def _on_save(self):
        """点击保存按钮"""
        if not self.current_save:
            messagebox.showwarning("提示", "当前没有打开任何存档文件！")
            return

        # 同步金钱
        self._sync_money_from_ui()

        try:
            self.current_save.save()
            messagebox.showinfo(
                "保存成功",
                f"存档已成功保存回文件:\n{self.current_save.filepath}\n\n"
                f"金钱: {self.current_save.money} 黄金\n"
                f"武将属性与装备已全部写入！"
            )
            self.lbl_status.configure(
                text=f"存档已保存: {self.current_save.filename}",
                foreground="#006600"
            )
        except Exception as e:
            messagebox.showerror("保存失败", f"写入文件时出错:\n{e}")

    def _on_save_as(self):
        """另存为新文件"""
        if not self.current_save:
            messagebox.showwarning("提示", "当前没有打开任何存档文件！")
            return

        self._sync_money_from_ui()

        new_path = filedialog.asksaveasfilename(
            title="另存为《三国志英杰传》存档",
            initialfile=self.current_save.filename,
            filetypes=[
                ("英杰传存档 (*.R3S)", "*.R3S"),
                ("所有文件 (*.*)", "*.*")
            ]
        )
        if new_path:
            try:
                self.current_save.save(new_path)
                self.lbl_filepath.configure(text=new_path, foreground="#2C3E50")
                messagebox.showinfo("另存为成功", f"文件已另存为:\n{new_path}")
            except Exception as e:
                messagebox.showerror("另存为失败", f"写入文件时出错:\n{e}")

    def _sync_money_from_ui(self):
        """将 UI 中的金钱数值同步到 SaveFile"""
        if not self.current_save:
            return
        try:
            val = int(self.money_var.get().strip())
            self.current_save.set_money(val)
            self.money_var.set(str(self.current_save.money))
        except ValueError:
            self.money_var.set(str(self.current_save.money))

    # ================= 界面分栏与编辑联动 =================

    def _show_editor_panel(self, visible: bool):
        """控制右侧编辑面板与占位提示的切换"""
        if visible:
            self.placeholder_frame.pack_forget()
            self.editor_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.editor_frame.pack_forget()
            self.placeholder_frame.pack(fill=tk.BOTH, expand=True)

    def _on_tree_select(self, event=None):
        """左侧表格选中武将事件"""
        selected = self.tree.selection()
        if not selected:
            self.selected_avatar = None
            self._show_editor_panel(False)
            return

        avatar_index = int(selected[0])
        if not self.current_save or avatar_index >= len(self.current_save.avatars):
            return

        self.selected_avatar = self.current_save.avatars[avatar_index]
        self._populate_avatar_editor(self.selected_avatar)
        self._show_editor_panel(True)

    def _populate_avatar_editor(self, a: Avatar):
        """将选定武将数据填入右侧编辑表单"""
        self._updating_form = True

        self.lbl_editor_name.configure(
            text=f"【{a.name}】 #{a.index:03d} ({a.hex_id})"
        )

        self.avatar_juntuan_var.set(a.juntuan_name)
        self.avatar_bingzhong_var.set(a.bingzhong_name)
        self.avatar_level_var.set(str(a.level))
        self.avatar_exp_var.set(str(a.exp))
        self.avatar_troop_var.set(str(a.troop))
        self.avatar_morale_var.set(str(a.morale))

        # 填入全部 8 格道具
        for i in range(8):
            it_id = a.item_ids[i]
            if it_id == 0xFF:
                self.item_vars[i].set("(空)")
            else:
                it_name = DAOJU_LIST[it_id] if it_id < len(DAOJU_LIST) else f"0x{it_id:02X}"
                self.item_vars[i].set(it_name)

        self._updating_form = False

    def _on_avatar_field_change(self, event=None):
        """右侧基本属性修改后，写回内存对象并同步刷新左侧列表"""
        if self._updating_form or not self.selected_avatar:
            return

        a = self.selected_avatar

        # 1. 所属军团
        a.set_juntuan(self.avatar_juntuan_var.get())

        # 2. 兵种
        a.set_bingzhong(self.avatar_bingzhong_var.get())

        # 3. 等级
        try:
            a.set_level(int(self.avatar_level_var.get().strip()))
        except ValueError:
            pass
        self.avatar_level_var.set(str(a.level))

        # 4. 经验
        try:
            a.set_exp(int(self.avatar_exp_var.get().strip()))
        except ValueError:
            pass
        self.avatar_exp_var.set(str(a.exp))

        # 5. 兵力
        try:
            a.set_troop(int(self.avatar_troop_var.get().strip()))
        except ValueError:
            pass
        self.avatar_troop_var.set(str(a.troop))

        # 6. 士气
        try:
            a.set_morale(int(self.avatar_morale_var.get().strip()))
        except ValueError:
            pass
        self.avatar_morale_var.set(str(a.morale))

        # 更新左侧表格当前行数据
        self._update_tree_row(a)

    def _on_item_slot_change(self, slot_idx: int):
        """道具下拉框选择变更事件"""
        if self._updating_form or not self.selected_avatar:
            return

        chosen = self.item_vars[slot_idx].get()
        self.selected_avatar.set_item_slot(slot_idx, chosen)
        self._update_tree_row(self.selected_avatar)

    def _clear_all_items(self):
        """清空当前武将所有 8 个道具格"""
        if not self.selected_avatar:
            return
        for i in range(8):
            self.selected_avatar.set_item_slot(i, 0xFF)
            self.item_vars[i].set("(空)")
        self._update_tree_row(self.selected_avatar)

    def _quick_max_avatar(self):
        """一键满级满兵力满士气"""
        if not self.selected_avatar:
            return
        a = self.selected_avatar
        a.set_level(99)
        a.set_exp(0)
        a.set_troop(6000)
        a.set_morale(100)

        self._populate_avatar_editor(a)
        self._update_tree_row(a)

    def _update_tree_row(self, a: Avatar):
        """实时更新 Treeview 中对应的单行内容"""
        iid = str(a.index)
        if self.tree.exists(iid):
            self.tree.item(
                iid,
                values=(
                    f"#{a.index:03d}",
                    a.name,
                    a.juntuan_name,
                    a.bingzhong_name,
                    a.level,
                    a.exp,
                    f"{a.troop:,}",
                    a.morale,
                    a.items_summary
                )
            )

    # ================= 列表筛选与排序 =================

    def _reset_filters(self):
        self.juntuan_var.set("全部军团")
        self.search_var.set("")
        self.has_items_var.set(False)
        self._refresh_table()

    def _refresh_table(self):
        if not self.current_save:
            return

        jt_filter = self.juntuan_var.get()
        kw_filter = self.search_var.get()
        has_items = self.has_items_var.get()

        filtered_list = self.current_save.filter_avatars(
            juntuan_filter=jt_filter,
            search_keyword=kw_filter,
            has_items_only=has_items
        )

        col = self.sort_column
        reverse = self.sort_descending

        def sort_key(a: Avatar):
            val = getattr(a, col, None)
            if val is None:
                if col == "juntuan":
                    return a.juntuan_name
                elif col == "bingzhong":
                    return a.bingzhong_name
                elif col == "items":
                    return len(a.item_names)
                return 0
            return val

        filtered_list.sort(key=sort_key, reverse=reverse)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for a in filtered_list:
            self.tree.insert(
                "",
                tk.END,
                iid=str(a.index),
                values=(
                    f"#{a.index:03d}",
                    a.name,
                    a.juntuan_name,
                    a.bingzhong_name,
                    a.level,
                    a.exp,
                    f"{a.troop:,}",
                    a.morale,
                    a.items_summary
                )
            )

        self.lbl_filtered_count.configure(
            text=f"{len(filtered_list)} / {len(self.current_save.avatars)} 人"
        )

        # 检查之前选中的武将是否还在筛选结果中
        if self.selected_avatar and self.tree.exists(str(self.selected_avatar.index)):
            self.tree.selection_set(str(self.selected_avatar.index))
            self._show_editor_panel(True)
        else:
            self.tree.selection_remove(self.tree.selection())
            self._show_editor_panel(False)

    def _on_sort_column(self, col: str):
        if self.sort_column == col:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = col
            self.sort_descending = False
        self._refresh_table()
