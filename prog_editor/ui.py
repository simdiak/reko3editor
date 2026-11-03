"""
《三国志英杰传》游戏程序与数据修改器 (Main.exe & Bakdata.r3 & Snr*m.r3 & Snr*d.r3) - Tkinter 界面
支持系统补丁开关、384位武将三维能力(武力/智力/统御)、全章节剧情对白台词以及战斗事件剧本指令修改与保存
"""

import os
import struct
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Optional, List, Tuple

from msave_editor.constants import AVATAR_NAMES, BINGZHONG_LIST, DAOJU_LIST, JUNTUAN_MAP
from prog_editor.patches import ALL_PATCHES, Patch
from prog_editor.patcher import GamePatcher
from prog_editor.bakdata import AvatarStats, FALLBACK_AVATAR_NAMES
from prog_editor.snr_manager import SnrManager, SnrChapter, TextItem, CHAPTER_TITLES
from prog_editor.snrd_manager import (
    SnrdManager, SnrdChapter, SnrdPage, SnrdParagraph, SnrdSection,
    ScriptInstruction, TRIGGER_DESCR, AI_TYPES, DIRECTIONS, CODE_STEPS, get_avatar_name
)
from prog_editor.deploy_dialog import DeployArmyDialog


class ProgEditorApp:
    """主程序、武将能力、剧情对白及战斗剧本指令修改器主界面"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("《三国志英杰传》程序与数据修改器 - Prog Editor")
        self.root.geometry("1160x780")
        self.root.minsize(980, 640)

        self.patcher: Optional[GamePatcher] = None
        self.check_vars: Dict[str, tk.BooleanVar] = {}

        # 武将能力编辑状态
        self.selected_avatar_stat: Optional[AvatarStats] = None
        self._updating_avatar_form = False
        self.avatar_sort_col = "index"
        self.avatar_sort_desc = False

        # 剧情对白编辑状态
        self.current_chapter: Optional[SnrChapter] = None
        self.selected_text_item: Optional[TextItem] = None
        self._updating_text_form = False
        self._cached_original_text = ""

        # 剧本指令 (SNRD) 编辑状态
        self.current_snrd_chapter: Optional[SnrdChapter] = None
        self.selected_instruction: Optional[ScriptInstruction] = None
        self.selected_ins_meta: Optional[Dict] = None
        self._updating_ins_form = False
        self._cached_original_ins_bytes = b""

        self._setup_style()
        self._build_ui()
        self._try_load_default_dir()

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        self.font_main = ('Sans', 10)
        self.font_bold = ('Sans', 10, 'bold')
        self.font_title = ('Sans', 11, 'bold')
        self.font_desc = ('Sans', 9)

        style.configure('TLabel', font=self.font_main)
        style.configure('TButton', font=self.font_main)
        style.configure('TCheckbutton', font=self.font_bold)
        style.configure('Primary.TButton', font=self.font_bold)
        style.configure('Category.TLabelframe', font=self.font_title)
        style.configure('Category.TLabelframe.Label', font=self.font_title)
        style.configure('Treeview', font=self.font_main, rowheight=25)
        style.configure('Treeview.Heading', font=self.font_bold)

    def _build_ui(self):
        """构建整体 UI 布局"""
        # ================= 1. 顶部游戏目录选择与校验 =================
        top_frame = ttk.LabelFrame(self.root, text=" 游戏根目录选择 ", padding=10)
        top_frame.pack(fill=tk.X, padx=12, pady=(8, 4))

        dir_btn_row = ttk.Frame(top_frame)
        dir_btn_row.pack(fill=tk.X)

        btn_browse = ttk.Button(
            dir_btn_row, text="📁 选择游戏目录...", command=self._on_browse_directory
        )
        btn_browse.pack(side=tk.LEFT, padx=(0, 8))

        btn_default = ttk.Button(
            dir_btn_row, text="快捷载入项目 reko3 目录", command=self._on_load_project_reko3
        )
        btn_default.pack(side=tk.LEFT, padx=(0, 15))

        self.lbl_exe_status = ttk.Label(
            dir_btn_row, text="请选择包含 Main.exe 的游戏目录", foreground="#888888", font=self.font_bold
        )
        self.lbl_exe_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_dir_path = ttk.Label(
            top_frame, text="当前未载入任何目录", foreground="#555555", font=('Sans', 9)
        )
        self.lbl_dir_path.pack(anchor="w", pady=(3, 0))

        # ================= 2. 中间多标签页工作区 =================
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # Tab 1: 战斗与系统功能补丁 (Main.exe)
        self.tab_patches = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.tab_patches, text="  ⚙ 战斗系统功能补丁 (Main.exe)  ")
        self._build_patches_tab(self.tab_patches)

        # Tab 2: 武将三项能力修改 (Bakdata.r3)
        self.tab_avatars = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.tab_avatars, text="  🎖 武将三项能力修改 (武力/智力/统御)  ")
        self._build_avatars_tab(self.tab_avatars)

        # Tab 3: 剧情文本与对白修改 (SNRM)
        self.tab_snrm = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.tab_snrm, text="  💬 剧情对白与台词修改 (SNRM)  ")
        self._build_snrm_tab(self.tab_snrm)

        # Tab 4: 战斗与事件剧本指令 (SNRD)
        self.tab_snrd = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.tab_snrd, text="  ⚔ 战斗与事件剧本指令 (SNRD)  ")
        self._build_snrd_tab(self.tab_snrd)

        # ================= 3. 底部操作按钮栏 =================
        bottom_frame = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        bottom_frame.pack(fill=tk.X)

        self.btn_restore = ttk.Button(
            bottom_frame, text="🔄 还原原版备份 (.bak)", command=self._on_restore_backup
        )
        self.btn_restore.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_save = ttk.Button(
            bottom_frame, text="💾 保存全部修改 (写回游戏目录)", style='Primary.TButton', command=self._on_save_all
        )
        self.btn_save.pack(side=tk.RIGHT)

        status_bar = ttk.Frame(self.root, relief="sunken", padding=(6, 3))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status = ttk.Label(
            status_bar,
            text="就绪。支持系统补丁、武将三维能力、剧情对白及战斗事件剧本指令编辑。",
            font=('Sans', 9)
        )
        self.lbl_status.pack(side=tk.LEFT)

    # ================= Tab 1: 系统补丁 UI =================

    def _build_patches_tab(self, parent: ttk.Frame):
        toolbar = ttk.Frame(parent, padding=(2, 0, 2, 4))
        toolbar.pack(fill=tk.X)

        btn_select_all = ttk.Button(toolbar, text="全选补丁", command=self._select_all_patches, width=10)
        btn_select_all.pack(side=tk.LEFT, padx=(0, 6))

        btn_clear_all = ttk.Button(toolbar, text="全不选", command=self._clear_all_patches, width=10)
        btn_clear_all.pack(side=tk.LEFT)

        ttk.Label(
            toolbar,
            text="提示: 勾选需要启用的功能，点击底部保存即可写回 Main.exe 并自动备份",
            foreground="#666666",
            font=self.font_desc
        ).pack(side=tk.RIGHT)

        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scroll_inner = ttk.Frame(canvas)

        canvas_win = canvas.create_window((0, 0), window=scroll_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_win, width=e.width)
        )

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        categories = []
        for p in ALL_PATCHES:
            if p.category not in categories:
                categories.append(p.category)

        for cat in categories:
            cat_frame = ttk.LabelFrame(scroll_inner, text=f" 【{cat}】 ", padding=8)
            cat_frame.pack(fill=tk.X, expand=True, pady=4, padx=4)

            cat_patches = [p for p in ALL_PATCHES if p.category == cat]
            for p in cat_patches:
                item_box = ttk.Frame(cat_frame, padding=(2, 3))
                item_box.pack(fill=tk.X, pady=2)

                var = tk.BooleanVar(value=False)
                self.check_vars[p.patch_id] = var

                chk = ttk.Checkbutton(
                    item_box,
                    text=p.name,
                    variable=var
                )
                chk.pack(anchor="w")

                desc_lbl = ttk.Label(
                    item_box,
                    text=f"    说明: {p.description}",
                    foreground="#555555",
                    font=self.font_desc,
                    wraplength=800
                )
                desc_lbl.pack(anchor="w", padx=(18, 0), pady=(1, 2))

    # ================= Tab 2: 武将三项能力 UI =================

    def _build_avatars_tab(self, parent: ttk.Frame):
        avatar_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        avatar_paned.pack(fill=tk.BOTH, expand=True)

        left_box = ttk.Frame(avatar_paned)
        avatar_paned.add(left_box, weight=2)

        search_bar = ttk.Frame(left_box, padding=(2, 0, 2, 6))
        search_bar.pack(fill=tk.X)

        ttk.Label(search_bar, text="搜索武将:").pack(side=tk.LEFT, padx=(0, 4))
        self.avatar_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_bar, textvariable=self.avatar_search_var, width=16)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.avatar_search_var.trace_add("write", lambda *args: self._refresh_avatar_table())

        btn_clear_search = ttk.Button(search_bar, text="清空", width=5, command=lambda: self.avatar_search_var.set(""))
        btn_clear_search.pack(side=tk.LEFT, padx=(0, 15))

        self.lbl_avatar_count = ttk.Label(search_bar, text="共 0 人", foreground="#666666")
        self.lbl_avatar_count.pack(side=tk.RIGHT)

        table_container = ttk.Frame(left_box)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = [
            ("index", "序号", 60, "center"),
            ("name", "武将姓名", 100, "center"),
            ("tongyu", "统御", 70, "center"),
            ("wuli", "武力", 70, "center"),
            ("zhili", "智力", 70, "center"),
            ("total", "三维总和", 85, "center"),
        ]

        self.avatar_tree = ttk.Treeview(
            table_container,
            columns=[col[0] for col in columns],
            show="headings",
            selectmode="browse"
        )

        for col_id, col_text, col_width, col_align in columns:
            self.avatar_tree.heading(
                col_id,
                text=col_text,
                command=lambda c=col_id: self._on_sort_avatar_column(c)
            )
            self.avatar_tree.column(col_id, width=col_width, anchor=col_align)

        v_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.avatar_tree.yview)
        self.avatar_tree.configure(yscrollcommand=v_scroll.set)

        self.avatar_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.avatar_tree.bind("<<TreeviewSelect>>", self._on_avatar_select)

        self.avatar_edit_box = ttk.LabelFrame(avatar_paned, text=" 武将能力编辑 ", padding=12)
        avatar_paned.add(self.avatar_edit_box, weight=1)

        self._build_avatar_edit_panel(self.avatar_edit_box)

    def _build_avatar_edit_panel(self, parent: ttk.LabelFrame):
        self.lbl_cur_avatar_title = ttk.Label(
            parent, text="【请在左侧选择武将】", font=self.font_title, foreground="#1B4F72"
        )
        self.lbl_cur_avatar_title.pack(anchor="w", pady=(0, 15))

        stat_grid = ttk.Frame(parent)
        stat_grid.pack(fill=tk.X, pady=(0, 15))
        stat_grid.columnconfigure(1, weight=1)

        ttk.Label(stat_grid, text="统御 (0~100):", font=self.font_bold).grid(
            row=0, column=0, sticky="w", padx=6, pady=8
        )
        self.stat_tongyu_var = tk.StringVar(value="0")
        self.stat_tongyu_spin = ttk.Spinbox(
            stat_grid, from_=0, to=100, textvariable=self.stat_tongyu_var, width=10
        )
        self.stat_tongyu_spin.grid(row=0, column=1, sticky="ew", padx=6, pady=8)
        self.stat_tongyu_spin.bind("<FocusOut>", self._on_stat_field_change)
        self.stat_tongyu_spin.bind("<Return>", self._on_stat_field_change)

        ttk.Label(stat_grid, text="武力 (0~100):", font=self.font_bold).grid(
            row=1, column=0, sticky="w", padx=6, pady=8
        )
        self.stat_wuli_var = tk.StringVar(value="0")
        self.stat_wuli_spin = ttk.Spinbox(
            stat_grid, from_=0, to=100, textvariable=self.stat_wuli_var, width=10
        )
        self.stat_wuli_spin.grid(row=1, column=1, sticky="ew", padx=6, pady=8)
        self.stat_wuli_spin.bind("<FocusOut>", self._on_stat_field_change)
        self.stat_wuli_spin.bind("<Return>", self._on_stat_field_change)

        ttk.Label(stat_grid, text="智力 (0~100):", font=self.font_bold).grid(
            row=2, column=0, sticky="w", padx=6, pady=8
        )
        self.stat_zhili_var = tk.StringVar(value="0")
        self.stat_zhili_spin = ttk.Spinbox(
            stat_grid, from_=0, to=100, textvariable=self.stat_zhili_var, width=10
        )
        self.stat_zhili_spin.grid(row=2, column=1, sticky="ew", padx=6, pady=8)
        self.stat_zhili_spin.bind("<FocusOut>", self._on_stat_field_change)
        self.stat_zhili_spin.bind("<Return>", self._on_stat_field_change)

        self.lbl_cur_total = ttk.Label(parent, text="三项能力总和: -", font=self.font_main)
        self.lbl_cur_total.pack(anchor="w", pady=(0, 15))

        btn_box = ttk.Frame(parent)
        btn_box.pack(fill=tk.X, pady=(0, 15))

        btn_max_current = ttk.Button(
            btn_box, text="⚡ 三项全满 100", command=self._set_current_avatar_max
        )
        btn_max_current.pack(fill=tk.X, pady=3)

        batch_group = ttk.LabelFrame(parent, text=" 批量能力增强 ", padding=8)
        batch_group.pack(fill=tk.X, pady=(10, 0))

        btn_batch_wuli = ttk.Button(
            batch_group, text="全员武力 +10", command=lambda: self._batch_boost("wuli", 10)
        )
        btn_batch_wuli.pack(fill=tk.X, pady=2)

        btn_batch_zhili = ttk.Button(
            batch_group, text="全员智力 +10", command=lambda: self._batch_boost("zhili", 10)
        )
        btn_batch_zhili.pack(fill=tk.X, pady=2)

        btn_batch_tongyu = ttk.Button(
            batch_group, text="全员统御 +10", command=lambda: self._batch_boost("tongyu", 10)
        )
        btn_batch_tongyu.pack(fill=tk.X, pady=2)

        btn_batch_all_max = ttk.Button(
            batch_group, text="⚡ 全员三维全部拉满 (100)", command=self._batch_boost_all_max
        )
        btn_batch_all_max.pack(fill=tk.X, pady=(6, 2))

    # ================= Tab 3: 剧情对白修改 (SNRM) =================

    def _build_snrm_tab(self, parent: ttk.Frame):
        top_bar = ttk.Frame(parent, padding=(2, 0, 2, 4))
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="选择章节:", font=self.font_bold).pack(side=tk.LEFT, padx=(0, 4))
        self.snrm_chapter_var = tk.StringVar(value="第0章: 序章")
        self.snrm_chapter_combo = ttk.Combobox(
            top_bar,
            textvariable=self.snrm_chapter_var,
            state="readonly",
            width=24
        )
        self.snrm_chapter_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.snrm_chapter_combo.bind("<<ComboboxSelected>>", self._on_chapter_selected)

        ttk.Label(top_bar, text="类型:").pack(side=tk.LEFT, padx=(0, 2))
        self.snrm_type_filter_var = tk.StringVar(value="全部")
        cb_type = ttk.Combobox(
            top_bar,
            textvariable=self.snrm_type_filter_var,
            values=["全部", "仅武将对白", "仅旁白/描述"],
            state="readonly",
            width=10
        )
        cb_type.pack(side=tk.LEFT, padx=(0, 12))
        cb_type.bind("<<ComboboxSelected>>", lambda e: self._refresh_text_table())

        ttk.Label(top_bar, text="搜索内容/武将:").pack(side=tk.LEFT, padx=(0, 2))
        self.snrm_search_var = tk.StringVar()
        entry_search = ttk.Entry(top_bar, textvariable=self.snrm_search_var, width=14)
        entry_search.pack(side=tk.LEFT, padx=(0, 6))
        self.snrm_search_var.trace_add("write", lambda *args: self._refresh_text_table())

        btn_clear_s = ttk.Button(top_bar, text="清空", width=4, command=lambda: self.snrm_search_var.set(""))
        btn_clear_s.pack(side=tk.LEFT, padx=(0, 15))

        btn_save_cur_ch = ttk.Button(
            top_bar, text="💾 保存当前章节", command=self._on_save_current_chapter
        )
        btn_save_cur_ch.pack(side=tk.RIGHT)

        self.lbl_snrm_count = ttk.Label(top_bar, text="共 0 条文本", foreground="#666666")
        self.lbl_snrm_count.pack(side=tk.RIGHT, padx=(0, 15))

        snrm_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        snrm_paned.pack(fill=tk.BOTH, expand=True)

        left_list_box = ttk.Frame(snrm_paned)
        snrm_paned.add(left_list_box, weight=3)

        columns = [
            ("index", "序号", 55, "center"),
            ("speaker", "说话人", 90, "center"),
            ("type", "类型", 75, "center"),
            ("preview", "对白 / 剧本内容预览", 340, "w"),
        ]

        self.text_tree = ttk.Treeview(
            left_list_box,
            columns=[col[0] for col in columns],
            show="headings",
            selectmode="browse"
        )

        for col_id, col_text, col_width, col_align in columns:
            self.text_tree.heading(col_id, text=col_text)
            self.text_tree.column(col_id, width=col_width, anchor=col_align, stretch=(col_id == "preview"))

        v_scroll = ttk.Scrollbar(left_list_box, orient=tk.VERTICAL, command=self.text_tree.yview)
        self.text_tree.configure(yscrollcommand=v_scroll.set)

        self.text_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_tree.bind("<<TreeviewSelect>>", self._on_text_select)

        self.text_edit_box = ttk.LabelFrame(snrm_paned, text=" 剧情对白内容编辑 ", padding=10)
        snrm_paned.add(self.text_edit_box, weight=2)

        self._build_text_edit_panel(self.text_edit_box)

    def _build_text_edit_panel(self, parent: ttk.LabelFrame):
        speaker_row = ttk.Frame(parent)
        speaker_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(speaker_row, text="说话人物:", font=self.font_bold).pack(side=tk.LEFT, padx=(0, 6))

        self.speaker_options = ["旁白 / 系统 (无头像)"] + list(FALLBACK_AVATAR_NAMES)
        self.speaker_var = tk.StringVar(value="旁白 / 系统 (无头像)")
        self.speaker_combo = ttk.Combobox(
            speaker_row,
            textvariable=self.speaker_var,
            values=self.speaker_options,
            state="readonly",
            width=18
        )
        self.speaker_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.speaker_combo.bind("<<ComboboxSelected>>", self._on_speaker_change)

        self.lbl_text_page_info = ttk.Label(
            speaker_row, text="所在Page: -", foreground="#888888", font=self.font_desc
        )
        self.lbl_text_page_info.pack(side=tk.RIGHT)

        ttk.Label(
            parent,
            text="可在下方直接编辑台词内容（支持多行排版与换行符）：",
            font=self.font_desc,
            foreground="#555555"
        ).pack(anchor="w", pady=(0, 4))

        text_container = ttk.Frame(parent)
        text_container.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.txt_content = tk.Text(
            text_container,
            wrap=tk.WORD,
            font=('Sans', 10),
            padx=8,
            pady=8,
            undo=True
        )
        txt_scroll = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.txt_content.yview)
        self.txt_content.configure(yscrollcommand=txt_scroll.set)

        self.txt_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_content.bind("<KeyRelease>", self._on_text_content_change)

        self.lbl_big5_status = ttk.Label(
            parent, text="✔ 编码校验: 符合 Big5 繁体规范", foreground="#008800", font=self.font_desc
        )
        self.lbl_big5_status.pack(anchor="w", pady=(0, 6))

        btn_actions = ttk.Frame(parent)
        btn_actions.pack(fill=tk.X)

        btn_revert_cur = ttk.Button(
            btn_actions, text="恢复本条原话", command=self._revert_current_text, width=12
        )
        btn_revert_cur.pack(side=tk.LEFT, padx=(0, 6))

        btn_strip = ttk.Button(
            btn_actions, text="去除首尾空行", command=self._strip_current_text, width=12
        )
        btn_strip.pack(side=tk.LEFT)

    # ================= Tab 4: 战斗与事件剧本指令 (SNRD) =================

    def _build_snrd_tab(self, parent: ttk.Frame):
        """构建战斗与事件剧本指令编辑选项卡"""
        # 顶部工具栏
        top_bar = ttk.Frame(parent, padding=(2, 0, 2, 4))
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="章节:", font=self.font_bold).pack(side=tk.LEFT, padx=(0, 4))
        self.snrd_chapter_var = tk.StringVar(value="第0章")
        self.snrd_chapter_combo = ttk.Combobox(
            top_bar,
            textvariable=self.snrd_chapter_var,
            state="readonly",
            width=22
        )
        self.snrd_chapter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.snrd_chapter_combo.bind("<<ComboboxSelected>>", self._on_snrd_chapter_selected)

        ttk.Label(top_bar, text="触发条件:").pack(side=tk.LEFT, padx=(0, 2))
        self.snrd_trigger_filter_var = tk.StringVar(value="全部")
        trigger_opts = ["全部"] + list(TRIGGER_DESCR.values())
        cb_trigger = ttk.Combobox(
            top_bar,
            textvariable=self.snrd_trigger_filter_var,
            values=trigger_opts,
            state="readonly",
            width=10
        )
        cb_trigger.pack(side=tk.LEFT, padx=(0, 10))
        cb_trigger.bind("<<ComboboxSelected>>", lambda e: self._refresh_instruction_table())

        ttk.Label(top_bar, text="指令类型:").pack(side=tk.LEFT, padx=(0, 2))
        self.snrd_op_filter_var = tk.StringVar(value="全部指令")
        op_opts = [
            "全部指令", "部署我军部队", "部署敌军部队", "武将单挑", "改变人物AI",
            "设置事件开关", "检查条件", "部署非战斗人物", "获得道具", "援军出现",
            "战斗胜利", "战斗失败"
        ]
        cb_op = ttk.Combobox(
            top_bar,
            textvariable=self.snrd_op_filter_var,
            values=op_opts,
            state="readonly",
            width=11
        )
        cb_op.pack(side=tk.LEFT, padx=(0, 10))
        cb_op.bind("<<ComboboxSelected>>", lambda e: self._refresh_instruction_table())

        ttk.Label(top_bar, text="搜索:").pack(side=tk.LEFT, padx=(0, 2))
        self.snrd_search_var = tk.StringVar()
        entry_s = ttk.Entry(top_bar, textvariable=self.snrd_search_var, width=12)
        entry_s.pack(side=tk.LEFT, padx=(0, 6))
        self.snrd_search_var.trace_add("write", lambda *args: self._refresh_instruction_table())

        btn_save_snrd = ttk.Button(
            top_bar, text="💾 保存当前剧本指令", command=self._on_save_current_snrd
        )
        btn_save_snrd.pack(side=tk.RIGHT)

        self.lbl_snrd_count = ttk.Label(top_bar, text="共 0 条指令", foreground="#666666")
        self.lbl_snrd_count.pack(side=tk.RIGHT, padx=(0, 10))

        # 中间左右分栏 (指令树 + 属性编辑)
        snrd_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        snrd_paned.pack(fill=tk.BOTH, expand=True)

        left_ins_box = ttk.Frame(snrd_paned)
        snrd_paned.add(left_ins_box, weight=3)

        ins_columns = [
            ("pos", "位置", 80, "center"),
            ("trigger", "触发条件", 85, "center"),
            ("opname", "指令名称", 100, "center"),
            ("detail", "中文释义 / 战斗参数", 260, "w"),
            ("hex", "字节码(Hex)", 110, "w"),
        ]

        self.ins_tree = ttk.Treeview(
            left_ins_box,
            columns=[col[0] for col in ins_columns],
            show="headings",
            selectmode="browse"
        )

        for col_id, col_text, col_width, col_align in ins_columns:
            self.ins_tree.heading(col_id, text=col_text)
            self.ins_tree.column(col_id, width=col_width, anchor=col_align, stretch=(col_id in ("detail", "hex")))

        v_scroll = ttk.Scrollbar(left_ins_box, orient=tk.VERTICAL, command=self.ins_tree.yview)
        self.ins_tree.configure(yscrollcommand=v_scroll.set)

        self.ins_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.ins_tree.bind("<<TreeviewSelect>>", self._on_instruction_select)
        self.ins_tree.bind("<Double-1>", self._on_ins_tree_double_click)

        # 右侧指令参数编辑卡片
        self.ins_edit_box = ttk.LabelFrame(snrd_paned, text=" 指令参数调试与修改 ", padding=10)
        snrd_paned.add(self.ins_edit_box, weight=2)

        self._build_ins_edit_panel(self.ins_edit_box)

        parent.bind("<Control-s>", lambda e: self._on_save_current_snrd())
        parent.bind("<Control-S>", lambda e: self._on_save_current_snrd())

    def _build_ins_edit_panel(self, parent: ttk.LabelFrame):
        """构建单个指令详细参数编辑面板"""
        self.lbl_ins_title = ttk.Label(
            parent, text="【请在左侧列表中选择指令】", font=self.font_title, foreground="#1B4F72"
        )
        self.lbl_ins_title.pack(anchor="w", pady=(0, 6))

        self.lbl_ins_detail_display = ttk.Label(
            parent, text="中文释义: -", font=self.font_bold, foreground="#006600", wraplength=380
        )
        self.lbl_ins_detail_display.pack(anchor="w", pady=(0, 10))

        # 十六进制字节码编辑行
        hex_box = ttk.LabelFrame(parent, text=" 十六进制机器码 (可直接修改) ", padding=8)
        hex_box.pack(fill=tk.X, pady=(0, 10))

        self.ins_hex_var = tk.StringVar()
        self.entry_ins_hex = ttk.Entry(hex_box, textvariable=self.ins_hex_var, font=('Monospace', 10))
        self.entry_ins_hex.pack(fill=tk.X, pady=(2, 4))
        self.entry_ins_hex.bind("<FocusOut>", self._on_hex_input_change)
        self.entry_ins_hex.bind("<Return>", self._on_hex_input_change)

        ttk.Label(
            hex_box,
            text="提示: 以空格分隔的十六进制字节 (如: 10 02 00 04 00)",
            foreground="#888888",
            font=self.font_desc
        ).pack(anchor="w")

        # 可视化参数快捷辅助区 (针对部队部署、单挑、改变AI、事件开关等)
        self.helper_frame = ttk.LabelFrame(parent, text=" 常用指令可视化参数设定 ", padding=8)
        self.helper_frame.pack(fill=tk.X, pady=(0, 10))

        # 0. 我军部队部署辅助 (0x03)
        self.friend_deploy_frame = ttk.Frame(self.helper_frame)
        self.lbl_f_deploy_info = ttk.Label(
            self.friend_deploy_frame, text="我军部队部署方案: 30人席位", font=self.font_bold, foreground="#1B4F72"
        )
        self.lbl_f_deploy_info.pack(anchor="w", pady=(0, 6))

        f_btn_row = ttk.Frame(self.friend_deploy_frame)
        f_btn_row.pack(fill=tk.X, pady=2)

        btn_open_f_deploy = ttk.Button(
            f_btn_row,
            text="⚔ 展开编辑我军 30 人详细部署 (阵容/主将/位置/出场)...",
            style="Primary.TButton",
            command=self._open_deploy_army_dialog
        )
        btn_open_f_deploy.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_save_f_deploy = ttk.Button(
            f_btn_row,
            text="💾 保存到文件",
            command=self._on_save_current_snrd
        )
        btn_save_f_deploy.pack(side=tk.LEFT)

        # 0.5 敌军部队部署辅助 (0x22)
        self.enemy_deploy_frame = ttk.Frame(self.helper_frame)
        self.lbl_e_deploy_info = ttk.Label(
            self.enemy_deploy_frame, text="敌军部队部署方案: 30人席位", font=self.font_bold, foreground="#8B0000"
        )
        self.lbl_e_deploy_info.pack(anchor="w", pady=(0, 6))

        e_btn_row = ttk.Frame(self.enemy_deploy_frame)
        e_btn_row.pack(fill=tk.X, pady=2)

        btn_open_e_deploy = ttk.Button(
            e_btn_row,
            text="🛡 展开编辑敌军 30 人详细部署 (阵容/兵种/等级/位置/AI)...",
            style="Primary.TButton",
            command=self._open_deploy_army_dialog
        )
        btn_open_e_deploy.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_save_e_deploy = ttk.Button(
            e_btn_row,
            text="💾 保存到文件",
            command=self._on_save_current_snrd
        )
        btn_save_e_deploy.pack(side=tk.LEFT)

        # 1. 单挑辅助 (0x10)
        self.duel_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.duel_frame, text="我方/发起武将:").grid(row=0, column=0, sticky="w", padx=2, pady=3)
        self.duel_a1_var = tk.StringVar()
        self.duel_a1_combo = ttk.Combobox(
            self.duel_frame, textvariable=self.duel_a1_var, values=list(AVATAR_NAMES), state="readonly", width=12
        )
        self.duel_a1_combo.grid(row=0, column=1, sticky="w", padx=2, pady=3)
        self.duel_a1_combo.bind("<<ComboboxSelected>>", self._on_duel_param_change)

        ttk.Label(self.duel_frame, text="敌方/迎战武将:").grid(row=1, column=0, sticky="w", padx=2, pady=3)
        self.duel_a2_var = tk.StringVar()
        self.duel_a2_combo = ttk.Combobox(
            self.duel_frame, textvariable=self.duel_a2_var, values=list(AVATAR_NAMES), state="readonly", width=12
        )
        self.duel_a2_combo.grid(row=1, column=1, sticky="w", padx=2, pady=3)
        self.duel_a2_combo.bind("<<ComboboxSelected>>", self._on_duel_param_change)

        # 2. 改变AI辅助 (0x1C)
        self.ai_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.ai_frame, text="目标武将:").grid(row=0, column=0, sticky="w", padx=2, pady=3)
        self.ai_target_var = tk.StringVar()
        self.ai_target_combo = ttk.Combobox(
            self.ai_frame, textvariable=self.ai_target_var, values=list(AVATAR_NAMES), state="readonly", width=12
        )
        self.ai_target_combo.grid(row=0, column=1, sticky="w", padx=2, pady=3)
        self.ai_target_combo.bind("<<ComboboxSelected>>", self._on_ai_param_change)

        ttk.Label(self.ai_frame, text="新AI模式:").grid(row=1, column=0, sticky="w", padx=2, pady=3)
        self.ai_mode_var = tk.StringVar()
        self.ai_mode_combo = ttk.Combobox(
            self.ai_frame, textvariable=self.ai_mode_var, values=list(AI_TYPES.values()), state="readonly", width=12
        )
        self.ai_mode_combo.grid(row=1, column=1, sticky="w", padx=2, pady=3)
        self.ai_mode_combo.bind("<<ComboboxSelected>>", self._on_ai_param_change)

        # 3. 部署非战斗人物/场景行动 (0x01, 0x0A)
        self.noncombat_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.noncombat_frame, text="行动人物:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.nc_avatar_var = tk.StringVar()
        self.nc_avatar_combo = ttk.Combobox(
            self.noncombat_frame, textvariable=self.nc_avatar_var, values=list(AVATAR_NAMES), state="readonly", width=12
        )
        self.nc_avatar_combo.grid(row=0, column=1, columnspan=3, sticky="w", padx=2, pady=2)
        self.nc_avatar_combo.bind("<<ComboboxSelected>>", self._on_noncombat_change)

        ttk.Label(self.noncombat_frame, text="X:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.nc_x_var = tk.IntVar(value=0)
        sp_nc_x = ttk.Spinbox(self.noncombat_frame, from_=0, to=99, textvariable=self.nc_x_var, width=5, command=self._on_noncombat_change)
        sp_nc_x.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        sp_nc_x.bind("<KeyRelease>", self._on_noncombat_change)

        ttk.Label(self.noncombat_frame, text="Y:").grid(row=1, column=2, sticky="w", padx=2, pady=2)
        self.nc_y_var = tk.IntVar(value=0)
        sp_nc_y = ttk.Spinbox(self.noncombat_frame, from_=0, to=99, textvariable=self.nc_y_var, width=5, command=self._on_noncombat_change)
        sp_nc_y.grid(row=1, column=3, sticky="w", padx=2, pady=2)
        sp_nc_y.bind("<KeyRelease>", self._on_noncombat_change)

        ttk.Label(self.noncombat_frame, text="朝向:").grid(row=2, column=0, sticky="w", padx=2, pady=2)
        self.nc_direct_var = tk.StringVar(value=DIRECTIONS[0])
        self.nc_direct_combo = ttk.Combobox(
            self.noncombat_frame, textvariable=self.nc_direct_var, values=list(DIRECTIONS.values()), state="readonly", width=12
        )
        self.nc_direct_combo.grid(row=2, column=1, columnspan=3, sticky="w", padx=2, pady=2)
        self.nc_direct_combo.bind("<<ComboboxSelected>>", self._on_noncombat_change)

        # 4. 事件开关 (0x14)
        self.event_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.event_frame, text="事件标志ID:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.ev_id_var = tk.IntVar(value=0)
        sp_ev = ttk.Spinbox(self.event_frame, from_=0, to=255, textvariable=self.ev_id_var, width=6, command=self._on_event_switch_change)
        sp_ev.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        sp_ev.bind("<KeyRelease>", self._on_event_switch_change)

        ttk.Label(self.event_frame, text="开关状态:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.ev_status_var = tk.StringVar(value="0: 关闭 (已触发/清除)")
        cb_ev = ttk.Combobox(
            self.event_frame, textvariable=self.ev_status_var,
            values=["0: 关闭 (已触发/清除)", "1: 开启 (未触发/生效)"],
            state="readonly", width=16
        )
        cb_ev.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        cb_ev.bind("<<ComboboxSelected>>", self._on_event_switch_change)

        # 5. 获得道具 (0x1B)
        self.item_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.item_frame, text="获得道具:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(
            self.item_frame, textvariable=self.item_var, values=list(DAOJU_LIST), state="readonly", width=14
        )
        self.item_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.item_combo.bind("<<ComboboxSelected>>", self._on_item_change)

        # 6. 单武将指令 (0x18 撤退, 0x1A 援军, 0x35 单挑人物)
        self.single_avatar_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.single_avatar_frame, text="关联武将:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.single_avatar_var = tk.StringVar()
        self.single_avatar_combo = ttk.Combobox(
            self.single_avatar_frame, textvariable=self.single_avatar_var, values=list(AVATAR_NAMES), state="readonly", width=14
        )
        self.single_avatar_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.single_avatar_combo.bind("<<ComboboxSelected>>", self._on_single_avatar_change)

        # 7. 阵营修改 (0x24, 0x28)
        self.faction_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.faction_frame, text="武将:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.faction_avatar_var = tk.StringVar()
        self.faction_avatar_combo = ttk.Combobox(
            self.faction_frame, textvariable=self.faction_avatar_var, values=list(AVATAR_NAMES), state="readonly", width=12
        )
        self.faction_avatar_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.faction_avatar_combo.bind("<<ComboboxSelected>>", self._on_faction_change)

        ttk.Label(self.faction_frame, text="目标阵营:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.faction_target_var = tk.StringVar()
        self.faction_target_combo = ttk.Combobox(
            self.faction_frame, textvariable=self.faction_target_var, values=list(JUNTUAN_MAP.values()), state="readonly", width=12
        )
        self.faction_target_combo.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        self.faction_target_combo.bind("<<ComboboxSelected>>", self._on_faction_change)

        # 8. 战场放火/放水 (0x27)
        self.fire_flood_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.fire_flood_frame, text="X:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.ff_x_var = tk.IntVar(value=0)
        sp_ff_x = ttk.Spinbox(self.fire_flood_frame, from_=0, to=99, textvariable=self.ff_x_var, width=5, command=self._on_fire_flood_change)
        sp_ff_x.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        sp_ff_x.bind("<KeyRelease>", self._on_fire_flood_change)

        ttk.Label(self.fire_flood_frame, text="Y:").grid(row=0, column=2, sticky="w", padx=2, pady=2)
        self.ff_y_var = tk.IntVar(value=0)
        sp_ff_y = ttk.Spinbox(self.fire_flood_frame, from_=0, to=99, textvariable=self.ff_y_var, width=5, command=self._on_fire_flood_change)
        sp_ff_y.grid(row=0, column=3, sticky="w", padx=2, pady=2)
        sp_ff_y.bind("<KeyRelease>", self._on_fire_flood_change)

        ttk.Label(self.fire_flood_frame, text="操作:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.ff_action_var = tk.StringVar(value="0: 放火")
        cb_ff = ttk.Combobox(
            self.fire_flood_frame, textvariable=self.ff_action_var, values=["0: 放火", "1: 放水", "2: 取消"],
            state="readonly", width=10
        )
        cb_ff.grid(row=1, column=1, columnspan=3, sticky="w", padx=2, pady=2)
        cb_ff.bind("<<ComboboxSelected>>", self._on_fire_flood_change)

        # 9. 剧情模式 (0x17)
        self.scenario_frame = ttk.Frame(self.helper_frame)
        ttk.Label(self.scenario_frame, text="剧情模式:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.scenario_var = tk.StringVar(value="1: 开启")
        cb_sc = ttk.Combobox(
            self.scenario_frame, textvariable=self.scenario_var, values=["0: 关闭", "1: 开启"],
            state="readonly", width=12
        )
        cb_sc.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        cb_sc.bind("<<ComboboxSelected>>", self._on_scenario_change)

        self.lbl_no_helper = ttk.Label(
            self.helper_frame, text="当前指令可通过上方直接修改十六进制字节码", foreground="#666666"
        )
        self.lbl_no_helper.pack(anchor="w", pady=4)

        # 操作按钮
        btn_box = ttk.Frame(parent)
        btn_box.pack(fill=tk.X, pady=(10, 0))

        btn_revert = ttk.Button(
            btn_box, text="恢复原始指令", command=self._revert_current_instruction, width=12
        )
        btn_revert.pack(side=tk.LEFT, padx=(0, 8))

        btn_save_ins = ttk.Button(
            btn_box, text="💾 保存剧本修改到文件", style="Primary.TButton", command=self._on_save_current_snrd
        )
        btn_save_ins.pack(side=tk.LEFT)

    # ================= 目录选择与数据载入 =================

    def _try_load_default_dir(self):
        default_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "backend", "reko3"
        )
        if os.path.isdir(default_dir):
            try:
                self._load_game_directory(default_dir)
            except Exception:
                pass

    def _on_load_project_reko3(self):
        proj_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "backend", "reko3"
        )
        if os.path.isdir(proj_dir):
            self._load_game_directory(proj_dir)
        else:
            messagebox.showwarning("提示", f"项目内置目录未找到:\n{proj_dir}")

    def _on_browse_directory(self):
        chosen_dir = filedialog.askdirectory(
            title="选择《三国志英杰传》游戏根目录（包含 Main.exe 与数据文件）"
        )
        if chosen_dir:
            self._load_game_directory(chosen_dir)

    def _load_game_directory(self, game_dir: str):
        try:
            patcher = GamePatcher(game_dir)
            self.patcher = patcher
        except (ValueError, FileNotFoundError) as e:
            messagebox.showerror("目录校验失败", str(e))
            self.lbl_exe_status.configure(
                text="❌ 校验失败: 目录下未找到合法的 Main.exe",
                foreground="#CC0000"
            )
            return

        file_size = os.path.getsize(patcher.exe_path)
        features = ["Main.exe"]
        if patcher.has_bakdata:
            features.append("Bakdata.r3 (武将能力)")
        if patcher.has_snr:
            features.append(f"Snr*m.r3 ({len(patcher.snr_manager.available_chapters)}章剧情)")
        if patcher.has_snrd:
            features.append(f"Snr*d.r3 ({len(patcher.snrd_manager.available_chapters)}章指令)")

        self.lbl_dir_path.configure(
            text=f"游戏目录: {patcher.game_dir}\n已连接: {', '.join(features)} | Main.exe: {file_size:,} 字节"
        )
        self.lbl_exe_status.configure(
            text="✔ 游戏程序、数据及剧本指令已就绪",
            foreground="#008800"
        )

        # 刷新四个模块
        states = patcher.get_patch_states()
        for patch_id, is_enabled in states.items():
            if patch_id in self.check_vars:
                self.check_vars[patch_id].set(is_enabled)

        self._refresh_avatar_table()
        self._setup_chapter_combo()
        self._setup_snrd_chapter_combo()

        self.lbl_status.configure(
            text=f"已成功载入目录: {patcher.game_dir}。全模块就绪。"
        )

    # ================= 剧本指令 (SNRD) 交互与联动 =================

    def _setup_snrd_chapter_combo(self):
        if not self.patcher or not self.patcher.snrd_manager:
            self.snrd_chapter_combo.configure(values=[])
            return

        chapters = self.patcher.snrd_manager.available_chapters
        combo_vals = []
        for ch in chapters:
            title = CHAPTER_TITLES.get(ch, f"第{ch}章")
            combo_vals.append(f"第 {ch} 章: {title} (Snr{ch}d.r3)")

        self.snrd_chapter_combo.configure(values=combo_vals)
        if combo_vals:
            self.snrd_chapter_combo.set(combo_vals[0])
            self._load_snrd_chapter(chapters[0])

    def _on_snrd_chapter_selected(self, event=None):
        sel = self.snrd_chapter_combo.get()
        if not sel:
            return
        ch_num = int(sel.split()[1])
        self._load_snrd_chapter(ch_num)

    def _load_snrd_chapter(self, ch_num: int):
        if not self.patcher or not self.patcher.snrd_manager:
            return
        chapter = self.patcher.snrd_manager.get_chapter(ch_num)
        self.current_snrd_chapter = chapter
        self.selected_instruction = None
        self.selected_ins_meta = None
        self._refresh_instruction_table()

    def _refresh_instruction_table(self):
        for item in self.ins_tree.get_children():
            self.ins_tree.delete(item)

        if not self.current_snrd_chapter:
            self.lbl_snrd_count.configure(text="未载入剧本指令")
            return

        ch = self.current_snrd_chapter
        trigger_filter = self.snrd_trigger_filter_var.get()
        op_filter = self.snrd_op_filter_var.get()
        kw = self.snrd_search_var.get().strip().lower()

        filtered_items = []
        global_ins_id = 0

        for p_idx, page in enumerate(ch.pages):
            for pg_idx, paragraph in enumerate(page.paragraphs):
                for s_idx, section in enumerate(paragraph.sections):
                    t_name = section.trigger_name
                    if trigger_filter != "全部" and t_name != trigger_filter:
                        continue

                    for i_idx, ins in enumerate(section.instructions):
                        pos_str = f"P{p_idx}-段{pg_idx}-节{s_idx}-#{i_idx+1}"
                        op_name = ins.opcode_name
                        detail_str = ins.detail

                        # 过滤指令类型
                        if op_filter == "部署我军部队" and ins.opcode != 0x03:
                            continue
                        elif op_filter == "部署敌军部队" and ins.opcode != 0x22:
                            continue
                        elif op_filter == "武将单挑" and ins.opcode != 0x10:
                            continue
                        elif op_filter == "改变人物AI" and ins.opcode != 0x1C:
                            continue
                        elif op_filter == "设置事件开关" and ins.opcode != 0x14:
                            continue
                        elif op_filter == "检查条件" and ins.opcode != 0x21:
                            continue
                        elif op_filter == "战斗胜利" and ins.opcode != 0x26:
                            continue
                        elif op_filter == "战斗失败" and ins.opcode != 0x29:
                            continue
                        elif op_filter == "部署非战斗人物" and ins.opcode not in (0x01, 0x0A):
                            continue
                        elif op_filter == "获得道具" and ins.opcode != 0x1B:
                            continue
                        elif op_filter == "援军出现" and ins.opcode != 0x1A:
                            continue

                        # 关键词搜索
                        if kw:
                            full_text = f"{pos_str} {t_name} {op_name} {detail_str} {ins.hex_code}".lower()
                            if kw not in full_text:
                                continue

                        meta = {
                            'id': global_ins_id,
                            'pos': pos_str,
                            'p_idx': p_idx,
                            'pg_idx': pg_idx,
                            's_idx': s_idx,
                            'i_idx': i_idx,
                            'section': section,
                            'instruction': ins
                        }
                        filtered_items.append(meta)
                        global_ins_id += 1

        self.ins_meta_list = filtered_items

        for item in filtered_items:
            ins = item['instruction']
            self.ins_tree.insert(
                "",
                tk.END,
                iid=str(item['id']),
                values=(
                    item['pos'],
                    item['section'].trigger_name,
                    ins.opcode_name,
                    ins.detail,
                    ins.hex_code
                )
            )

        self.lbl_snrd_count.configure(
            text=f"显示 {len(filtered_items)} 条指令"
        )

        children = self.ins_tree.get_children()
        if children:
            self.ins_tree.selection_set(children[0])
            self._on_instruction_select()

    def _on_instruction_select(self, event=None):
        selected = self.ins_tree.selection()
        if not selected or not hasattr(self, 'ins_meta_list'):
            return

        sel_id = int(selected[0])
        meta = None
        for m in self.ins_meta_list:
            if m['id'] == sel_id:
                meta = m
                break
        if not meta:
            return

        self.selected_ins_meta = meta
        ins = meta['instruction']
        self.selected_instruction = ins
        self._cached_original_ins_bytes = bytes(ins.raw_bytes)

        self._updating_ins_form = True

        self.lbl_ins_title.configure(
            text=f"【{meta['pos']}】 触发: {meta['section'].trigger_name} | {ins.opcode_name}"
        )
        self.lbl_ins_detail_display.configure(
            text=f"中文释义: {ins.detail or '(基础控制指令)'}"
        )
        self.ins_hex_var.set(ins.hex_code)

        # 切换可视化辅助卡片
        self._update_helper_panels(ins)
        self._updating_ins_form = False

    def _on_ins_tree_double_click(self, event=None):
        """双击指令树某一行：如果是部署指令则快速弹出展开编辑器"""
        if self.selected_instruction and self.selected_instruction.opcode in (0x03, 0x22):
            self._open_deploy_army_dialog()

    def _open_deploy_army_dialog(self):
        """打开部队部署 30 席位展开详细配置对话框"""
        if not self.selected_instruction:
            return
        DeployArmyDialog(
            self.root,
            self.selected_instruction,
            on_applied=self._on_deployment_dialog_applied
        )

    def _on_deployment_dialog_applied(self):
        """部队部署对话框保存后的界面刷新回调"""
        if self.selected_instruction:
            self.ins_hex_var.set(self.selected_instruction.hex_code)
            self.lbl_ins_detail_display.configure(
                text=f"中文释义: {self.selected_instruction.detail or '(基础控制指令)'}"
            )
            self._update_helper_panels(self.selected_instruction)
            self._update_ins_tree_row()

    def _update_helper_panels(self, ins: ScriptInstruction):
        """根据当前指令类型切换右侧可视化微调框"""
        self.duel_frame.pack_forget()
        self.ai_frame.pack_forget()
        self.friend_deploy_frame.pack_forget()
        self.enemy_deploy_frame.pack_forget()
        self.noncombat_frame.pack_forget()
        self.event_frame.pack_forget()
        self.item_frame.pack_forget()
        self.single_avatar_frame.pack_forget()
        self.faction_frame.pack_forget()
        self.fire_flood_frame.pack_forget()
        self.scenario_frame.pack_forget()
        self.lbl_no_helper.pack_forget()

        c = ins.opcode
        buf = ins.raw_bytes

        if c == 0x03 and len(buf) >= 12:  # 我军部队部署
            self.lbl_f_deploy_info.configure(text=ins.detail)
            self.friend_deploy_frame.pack(fill=tk.X, pady=4)

        elif c == 0x22 and len(buf) >= 2:  # 敌军部队部署
            self.lbl_e_deploy_info.configure(text=ins.detail)
            self.enemy_deploy_frame.pack(fill=tk.X, pady=4)

        elif c == 0x10 and len(buf) >= 5:  # 单挑
            a1 = struct.unpack('<H', buf[1:3])[0]
            a2 = struct.unpack('<H', buf[3:5])[0]
            n1 = get_avatar_name(a1)
            n2 = get_avatar_name(a2)
            if n1 in AVATAR_NAMES:
                self.duel_a1_var.set(n1)
            if n2 in AVATAR_NAMES:
                self.duel_a2_var.set(n2)
            self.duel_frame.pack(fill=tk.X, pady=2)

        elif c == 0x1C and len(buf) >= 4:  # 改变AI
            aid = struct.unpack('<H', buf[1:3])[0]
            n = get_avatar_name(aid)
            if n in AVATAR_NAMES:
                self.ai_target_var.set(n)
            ai_mode_name = AI_TYPES.get(buf[3], "原地警戒(攻击)")
            self.ai_mode_var.set(ai_mode_name)
            self.ai_frame.pack(fill=tk.X, pady=2)

        elif c in (0x01, 0x0A) and len(buf) >= 6:  # 部署非战斗人物/场景行动
            aid = struct.unpack('<H', buf[1:3])[0]
            n = get_avatar_name(aid)
            if n in AVATAR_NAMES:
                self.nc_avatar_var.set(n)
            self.nc_x_var.set(buf[3])
            self.nc_y_var.set(buf[4])
            self.nc_direct_var.set(DIRECTIONS.get(buf[5], DIRECTIONS[0]))
            self.noncombat_frame.pack(fill=tk.X, pady=2)

        elif c == 0x14 and len(buf) >= 3:  # 事件开关
            self.ev_id_var.set(buf[1])
            self.ev_status_var.set("1: 开启 (未触发/生效)" if buf[2] == 1 else "0: 关闭 (已触发/清除)")
            self.event_frame.pack(fill=tk.X, pady=2)

        elif c == 0x1B and len(buf) >= 2:  # 获得道具
            it_id = buf[1]
            it_name = DAOJU_LIST[it_id] if it_id < len(DAOJU_LIST) else DAOJU_LIST[0]
            self.item_var.set(it_name)
            self.item_frame.pack(fill=tk.X, pady=2)

        elif c in (0x18, 0x1A, 0x35) and len(buf) >= 3:  # 撤退/援军/单挑人物
            aid = struct.unpack('<H', buf[1:3])[0]
            n = get_avatar_name(aid)
            if n in AVATAR_NAMES:
                self.single_avatar_var.set(n)
            self.single_avatar_frame.pack(fill=tk.X, pady=2)

        elif c in (0x24, 0x28) and len(buf) >= 4:  # 改变阵营
            aid = struct.unpack('<H', buf[1:3])[0]
            n = get_avatar_name(aid)
            if n in AVATAR_NAMES:
                self.faction_avatar_var.set(n)
            f_name = JUNTUAN_MAP.get(buf[3] + 0x80, JUNTUAN_MAP[0x80])
            self.faction_target_var.set(f_name)
            self.faction_frame.pack(fill=tk.X, pady=2)

        elif c == 0x27 and len(buf) >= 4:  # 放火/放水
            self.ff_x_var.set(buf[1])
            self.ff_y_var.set(buf[2])
            act_str = "0: 放火" if buf[3] == 0 else ("1: 放水" if buf[3] == 1 else "2: 取消")
            self.ff_action_var.set(act_str)
            self.fire_flood_frame.pack(fill=tk.X, pady=2)

        elif c == 0x17 and len(buf) >= 2:  # 剧情模式
            self.scenario_var.set("1: 开启" if buf[1] == 1 else "0: 关闭")
            self.scenario_frame.pack(fill=tk.X, pady=2)

        else:
            self.lbl_no_helper.pack(anchor="w", pady=4)

    def _on_duel_param_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        n1 = self.duel_a1_var.get()
        n2 = self.duel_a2_var.get()
        if n1 in AVATAR_NAMES and n2 in AVATAR_NAMES:
            id1 = AVATAR_NAMES.index(n1)
            id2 = AVATAR_NAMES.index(n2)
            b = self.selected_instruction.raw_bytes
            struct.pack_into('<H', b, 1, id1)
            struct.pack_into('<H', b, 3, id2)
            self.ins_hex_var.set(self.selected_instruction.hex_code)
            self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
            self._update_ins_tree_row()

    def _on_ai_param_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        target_name = self.ai_target_var.get()
        mode_name = self.ai_mode_var.get()
        if target_name in AVATAR_NAMES:
            aid = AVATAR_NAMES.index(target_name)
            mode_id = 0
            for k, v in AI_TYPES.items():
                if v == mode_name:
                    mode_id = k
                    break
            b = self.selected_instruction.raw_bytes
            struct.pack_into('<H', b, 1, aid)
            b[3] = mode_id
            self.ins_hex_var.set(self.selected_instruction.hex_code)
            self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
            self._update_ins_tree_row()

    def _on_noncombat_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        name = self.nc_avatar_var.get()
        if name in AVATAR_NAMES:
            struct.pack_into('<H', b, 1, AVATAR_NAMES.index(name))
        try:
            b[3] = int(self.nc_x_var.get()) & 0xFF
            b[4] = int(self.nc_y_var.get()) & 0xFF
        except (ValueError, tk.TclError):
            pass
        d_name = self.nc_direct_var.get()
        for k, v in DIRECTIONS.items():
            if v == d_name:
                b[5] = k
                break
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_event_switch_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        try:
            b[1] = int(self.ev_id_var.get()) & 0xFF
        except (ValueError, tk.TclError):
            pass
        b[2] = 1 if "1:" in self.ev_status_var.get() else 0
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_item_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        name = self.item_var.get()
        if name in DAOJU_LIST:
            b[1] = DAOJU_LIST.index(name)
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_single_avatar_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        name = self.single_avatar_var.get()
        if name in AVATAR_NAMES:
            struct.pack_into('<H', b, 1, AVATAR_NAMES.index(name))
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_faction_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        name = self.faction_avatar_var.get()
        if name in AVATAR_NAMES:
            struct.pack_into('<H', b, 1, AVATAR_NAMES.index(name))
        f_name = self.faction_target_var.get()
        for k, v in JUNTUAN_MAP.items():
            if v == f_name:
                b[3] = (k - 0x80) & 0xFF
                break
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_fire_flood_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        try:
            b[1] = int(self.ff_x_var.get()) & 0xFF
            b[2] = int(self.ff_y_var.get()) & 0xFF
        except (ValueError, tk.TclError):
            pass
        act = self.ff_action_var.get()
        b[3] = 0 if "0:" in act else (1 if "1:" in act else 2)
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_scenario_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return
        b = self.selected_instruction.raw_bytes
        b[1] = 1 if "1:" in self.scenario_var.get() else 0
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail}")
        self._update_ins_tree_row()

    def _on_hex_input_change(self, event=None):
        if self._updating_ins_form or not self.selected_instruction:
            return

        hex_text = self.ins_hex_var.get().strip()
        parts = hex_text.split()
        try:
            new_bytes = bytes([int(p, 16) for p in parts])
            if len(new_bytes) != len(self.selected_instruction.raw_bytes):
                messagebox.showwarning(
                    "长度不匹配",
                    f"当前指令长度应为 {len(self.selected_instruction.raw_bytes)} 字节，"
                    f"输入了 {len(new_bytes)} 字节！请保持指令长度一致以防错位。"
                )
                self.ins_hex_var.set(self.selected_instruction.hex_code)
                return

            self.selected_instruction.raw_bytes = bytearray(new_bytes)
            self.selected_instruction.opcode = new_bytes[0]
            self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail or '(基础控制指令)'}")
            self._update_helper_panels(self.selected_instruction)
            self._update_ins_tree_row()
        except ValueError:
            messagebox.showerror("格式错误", "十六进制输入有误，请确保为 00~FF 的合法字符！")
            self.ins_hex_var.set(self.selected_instruction.hex_code)

    def _update_ins_tree_row(self):
        if not self.selected_ins_meta:
            return
        meta = self.selected_ins_meta
        ins = self.selected_instruction
        iid = str(meta['id'])
        if self.ins_tree.exists(iid):
            self.ins_tree.item(
                iid,
                values=(
                    meta['pos'],
                    meta['section'].trigger_name,
                    ins.opcode_name,
                    ins.detail,
                    ins.hex_code
                )
            )

    def _revert_current_instruction(self):
        if not self.selected_instruction or not self._cached_original_ins_bytes:
            return
        self.selected_instruction.raw_bytes = bytearray(self._cached_original_ins_bytes)
        self.selected_instruction.opcode = self._cached_original_ins_bytes[0]
        self.ins_hex_var.set(self.selected_instruction.hex_code)
        self.lbl_ins_detail_display.configure(text=f"中文释义: {self.selected_instruction.detail or '(基础控制指令)'}")
        self._update_helper_panels(self.selected_instruction)
        self._update_ins_tree_row()

    def _on_save_current_snrd(self):
        if not self.current_snrd_chapter:
            messagebox.showwarning("提示", "当前未载入任何剧本指令章节！")
            return
        try:
            self.current_snrd_chapter.save()
            messagebox.showinfo(
                "剧本指令保存成功",
                f"已成功将战斗与事件指令写回剧本文件:\n{self.current_snrd_chapter.file_path}\n\n"
                f"原始剧本已自动备份为: {self.current_snrd_chapter.filename}.bak"
            )
            self.lbl_status.configure(
                text=f"已保存剧本指令: {self.current_snrd_chapter.filename}",
                foreground="#006600"
            )
        except Exception as e:
            messagebox.showerror("保存失败", f"写入剧本指令时出错:\n{e}")

    # ================= 剧情对白逻辑 (SNRM) =================

    def _setup_chapter_combo(self):
        if not self.patcher or not self.patcher.snr_manager:
            self.snrm_chapter_combo.configure(values=[])
            return

        chapters = self.patcher.snr_manager.available_chapters
        combo_vals = []
        for ch in chapters:
            title = CHAPTER_TITLES.get(ch, f"第{ch}章")
            combo_vals.append(f"第 {ch} 章: {title} (Snr{ch}m.r3)")

        self.snrm_chapter_combo.configure(values=combo_vals)
        if combo_vals:
            self.snrm_chapter_combo.set(combo_vals[0])
            self._load_chapter(chapters[0])

    def _on_chapter_selected(self, event=None):
        sel = self.snrm_chapter_combo.get()
        if not sel:
            return
        ch_num = int(sel.split()[1])
        self._load_chapter(ch_num)

    def _load_chapter(self, ch_num: int):
        if not self.patcher or not self.patcher.snr_manager:
            return
        chapter = self.patcher.snr_manager.get_chapter(ch_num)
        self.current_chapter = chapter
        self.selected_text_item = None
        self._refresh_text_table()

    def _refresh_text_table(self):
        for item in self.text_tree.get_children():
            self.text_tree.delete(item)

        if not self.current_chapter:
            self.lbl_snrm_count.configure(text="未载入剧本文本")
            return

        items = self.current_chapter.items
        type_filter = self.snrm_type_filter_var.get()
        kw = self.snrm_search_var.get().strip().lower()

        filtered = []
        for it in items:
            if type_filter == "仅武将对白" and not it.is_dialogue:
                continue
            if type_filter == "仅旁白/描述" and it.is_dialogue:
                continue
            if kw:
                if kw not in it.text.lower() and kw not in it.speaker_name.lower():
                    continue
            filtered.append(it)

        for it in filtered:
            self.text_tree.insert(
                "",
                tk.END,
                iid=str(it.index),
                values=(
                    f"#{it.index+1:03d}",
                    it.speaker_name,
                    it.type_desc,
                    it.preview
                )
            )

        self.lbl_snrm_count.configure(
            text=f"显示 {len(filtered)} / {len(items)} 条"
        )

        children = self.text_tree.get_children()
        if children:
            self.text_tree.selection_set(children[0])
            self._on_text_select()

    def _on_text_select(self, event=None):
        selected = self.text_tree.selection()
        if not selected or not self.current_chapter:
            return

        idx = int(selected[0])
        it = self.current_chapter.items[idx]
        self.selected_text_item = it
        self._cached_original_text = it.text

        self._updating_text_form = True

        if it.is_dialogue and it.avatar_id is not None:
            if it.avatar_id < len(FALLBACK_AVATAR_NAMES):
                name = FALLBACK_AVATAR_NAMES[it.avatar_id]
            else:
                name = f"武将_{it.avatar_id}"
            if name in self.speaker_options:
                self.speaker_var.set(name)
            else:
                self.speaker_var.set("旁白 / 系统 (无头像)")
        else:
            self.speaker_var.set("旁白 / 系统 (无头像)")

        self.lbl_text_page_info.configure(
            text=f"所在 Page: {it.page} | 记录编号: #{it.index+1}"
        )

        self.txt_content.delete("1.0", tk.END)
        self.txt_content.insert("1.0", it.text)

        self._check_big5_status(it.text)
        self._updating_text_form = False

    def _on_speaker_change(self, event=None):
        if self._updating_text_form or not self.selected_text_item:
            return

        chosen = self.speaker_var.get()
        if chosen == "旁白 / 系统 (无头像)":
            self.selected_text_item.is_dialogue = False
            self.selected_text_item.avatar_id = None
        else:
            self.selected_text_item.is_dialogue = True
            if chosen in FALLBACK_AVATAR_NAMES:
                self.selected_text_item.avatar_id = FALLBACK_AVATAR_NAMES.index(chosen)
            else:
                self.selected_text_item.avatar_id = 0

        self._update_text_tree_row(self.selected_text_item)

    def _on_text_content_change(self, event=None):
        if self._updating_text_form or not self.selected_text_item:
            return

        new_text = self.txt_content.get("1.0", tk.END)
        if new_text.endswith("\n"):
            new_text = new_text[:-1]

        self.selected_text_item.text = new_text
        self._check_big5_status(new_text)
        self._update_text_tree_row(self.selected_text_item)

    def _check_big5_status(self, text: str):
        try:
            text.encode("big5")
            self.lbl_big5_status.configure(
                text="✔ 编码校验: 符合 Big5 繁体规范",
                foreground="#008800"
            )
        except UnicodeEncodeError as e:
            bad_char = text[e.start:e.end]
            self.lbl_big5_status.configure(
                text=f"⚠️ 提示: 包含非 Big5 繁体字符 '{bad_char}'，游戏读取可能出现乱码，建议替换为对应繁体字",
                foreground="#B8860B"
            )

    def _update_text_tree_row(self, it: TextItem):
        iid = str(it.index)
        if self.text_tree.exists(iid):
            self.text_tree.item(
                iid,
                values=(
                    f"#{it.index+1:03d}",
                    it.speaker_name,
                    it.type_desc,
                    it.preview
                )
            )

    def _revert_current_text(self):
        if not self.selected_text_item or not self._cached_original_text:
            return
        self.selected_text_item.text = self._cached_original_text
        self.txt_content.delete("1.0", tk.END)
        self.txt_content.insert("1.0", self._cached_original_text)
        self._check_big5_status(self._cached_original_text)
        self._update_text_tree_row(self.selected_text_item)

    def _strip_current_text(self):
        if not self.selected_text_item:
            return
        stripped = self.selected_text_item.text.strip("\r\n ")
        self.selected_text_item.text = stripped
        self.txt_content.delete("1.0", tk.END)
        self.txt_content.insert("1.0", stripped)
        self._check_big5_status(stripped)
        self._update_text_tree_row(self.selected_text_item)

    def _on_save_current_chapter(self):
        if not self.current_chapter:
            messagebox.showwarning("提示", "当前未载入任何剧本章节！")
            return
        try:
            self.current_chapter.save()
            messagebox.showinfo(
                "章节保存成功",
                f"已成功将对白写回剧本文件:\n{self.current_chapter.file_path}\n\n"
                f"原始剧本已自动备份为: {self.current_chapter.filename}.bak"
            )
            self.lbl_status.configure(
                text=f"已保存章节: {self.current_chapter.filename} ({len(self.current_chapter.items)} 条文本)",
                foreground="#006600"
            )
        except Exception as e:
            messagebox.showerror("保存失败", f"写入文件时出错:\n{e}")

    # ================= 武将三项能力操作联动 (Bakdata.r3) =================

    def _refresh_avatar_table(self):
        for item in self.avatar_tree.get_children():
            self.avatar_tree.delete(item)

        if not self.patcher or not self.patcher.bak_manager:
            self.lbl_avatar_count.configure(text="未载入武将数据")
            return

        avatars = self.patcher.bak_manager.avatars
        kw = self.avatar_search_var.get().strip().lower()

        filtered = avatars
        if kw:
            filtered = [
                a for a in avatars
                if kw in a.name.lower() or kw in str(a.index)
            ]

        col = self.avatar_sort_col
        rev = self.avatar_sort_desc
        filtered.sort(key=lambda a: getattr(a, col), reverse=rev)

        for a in filtered:
            self.avatar_tree.insert(
                "",
                tk.END,
                iid=str(a.index),
                values=(
                    f"#{a.index:03d}",
                    a.name,
                    a.tongyu,
                    a.wuli,
                    a.zhili,
                    a.total
                )
            )

        self.lbl_avatar_count.configure(
            text=f"显示 {len(filtered)} / {len(avatars)} 人"
        )

        if self.selected_avatar_stat and self.avatar_tree.exists(str(self.selected_avatar_stat.index)):
            self.avatar_tree.selection_set(str(self.selected_avatar_stat.index))
        else:
            children = self.avatar_tree.get_children()
            if children:
                self.avatar_tree.selection_set(children[0])
                self._on_avatar_select()

    def _on_sort_avatar_column(self, col: str):
        if self.avatar_sort_col == col:
            self.avatar_sort_desc = not self.avatar_sort_desc
        else:
            self.avatar_sort_col = col
            self.avatar_sort_desc = False
        self._refresh_avatar_table()

    def _on_avatar_select(self, event=None):
        selected = self.avatar_tree.selection()
        if not selected or not self.patcher or not self.patcher.bak_manager:
            return

        idx = int(selected[0])
        a = self.patcher.bak_manager.avatars[idx]
        self.selected_avatar_stat = a

        self._updating_avatar_form = True
        self.lbl_cur_avatar_title.configure(
            text=f"#{a.index:03d} 【{a.name}】"
        )
        self.stat_tongyu_var.set(str(a.tongyu))
        self.stat_wuli_var.set(str(a.wuli))
        self.stat_zhili_var.set(str(a.zhili))
        self.lbl_cur_total.configure(text=f"三项能力总和: {a.total}")
        self._updating_avatar_form = False

    def _on_stat_field_change(self, event=None):
        if self._updating_avatar_form or not self.selected_avatar_stat:
            return

        a = self.selected_avatar_stat
        try:
            a.tongyu = max(0, min(100, int(self.stat_tongyu_var.get().strip())))
        except ValueError:
            pass
        try:
            a.wuli = max(0, min(100, int(self.stat_wuli_var.get().strip())))
        except ValueError:
            pass
        try:
            a.zhili = max(0, min(100, int(self.stat_zhili_var.get().strip())))
        except ValueError:
            pass

        self.stat_tongyu_var.set(str(a.tongyu))
        self.stat_wuli_var.set(str(a.wuli))
        self.stat_zhili_var.set(str(a.zhili))
        self.lbl_cur_total.configure(text=f"三项能力总和: {a.total}")

        iid = str(a.index)
        if self.avatar_tree.exists(iid):
            self.avatar_tree.item(
                iid,
                values=(
                    f"#{a.index:03d}",
                    a.name,
                    a.tongyu,
                    a.wuli,
                    a.zhili,
                    a.total
                )
            )

    def _set_current_avatar_max(self):
        if not self.selected_avatar_stat:
            return
        a = self.selected_avatar_stat
        a.tongyu = 100
        a.wuli = 100
        a.zhili = 100
        self._on_avatar_select()
        self.avatar_tree.item(
            str(a.index),
            values=(f"#{a.index:03d}", a.name, 100, 100, 100, 300)
        )

    def _batch_boost(self, attr: str, boost_val: int):
        if not self.patcher or not self.patcher.bak_manager:
            return
        for a in self.patcher.bak_manager.avatars:
            cur = getattr(a, attr)
            setattr(a, attr, min(100, cur + boost_val))

        self._refresh_avatar_table()
        if self.selected_avatar_stat:
            self._on_avatar_select()

        messagebox.showinfo("批量增强完成", f"全员 {attr} 已全部 +{boost_val}（上限 100）！")

    def _batch_boost_all_max(self):
        if not self.patcher or not self.patcher.bak_manager:
            return
        if not messagebox.askyesno("批量操作确认", "确定要将全游戏 384 名武将的武力、智力、统御全部设为 100 吗？"):
            return

        for a in self.patcher.bak_manager.avatars:
            a.tongyu = 100
            a.wuli = 100
            a.zhili = 100

        self._refresh_avatar_table()
        if self.selected_avatar_stat:
            self._on_avatar_select()

        messagebox.showinfo("操作完成", "全员 384 名武将三项能力已全部拉满 100！")

    # ================= 补丁操作与保存 =================

    def _select_all_patches(self):
        for var in self.check_vars.values():
            var.set(True)

    def _clear_all_patches(self):
        for var in self.check_vars.values():
            var.set(False)

    def _on_save_all(self):
        """统一保存 Main.exe 补丁、Bakdata.r3、剧情对白(SNRM)及剧本指令(SNRD)"""
        if not self.patcher:
            messagebox.showwarning("提示", "请先选择游戏目录！")
            return

        desired_states = {
            patch_id: var.get() for patch_id, var in self.check_vars.items()
        }

        try:
            self.patcher.apply_and_save(desired_states, save_bakdata=True, save_snr=True, save_snrd=True)
            enabled_count = sum(1 for v in desired_states.values() if v)

            details = [f"✔ Main.exe: 已启用 {enabled_count} 项补丁"]
            if self.patcher.has_bakdata:
                details.append("✔ Bakdata.r3: 武将三项能力已写回")
            if self.patcher.has_snr:
                details.append(f"✔ Snr*m.r3: {len(self.patcher.snr_manager.available_chapters)} 个章节剧情文本已写回")
            if self.patcher.has_snrd:
                details.append(f"✔ Snr*d.r3: {len(self.patcher.snrd_manager.available_chapters)} 个章节剧本指令已写回")

            messagebox.showinfo(
                "全部保存成功",
                f"已成功将所有修改写回游戏目录:\n{self.patcher.game_dir}\n\n" +
                "\n".join(details) +
                "\n\n所有文件均已自动生成 .bak 原始备份。"
            )
            self.lbl_status.configure(
                text=f"全部保存成功！系统补丁、武将三维、剧情台词及剧本事件指令已全部持久化。",
                foreground="#006600"
            )
        except Exception as e:
            messagebox.showerror("保存失败", f"保存过程中发生错误:\n{e}")

    def _on_restore_backup(self):
        if not self.patcher:
            messagebox.showwarning("提示", "请先选择游戏目录！")
            return

        confirm = messagebox.askyesno(
            "确认还原",
            "确定要从备份文件 (.bak) 还原原始文件吗？\n"
            "将还原 Main.exe、Bakdata.r3、剧情对白(SNRM)及剧本指令(SNRD)为官方原版。"
        )
        if confirm:
            try:
                restored = self.patcher.restore_from_backup()
                states = self.patcher.get_patch_states()
                for patch_id, is_enabled in states.items():
                    if patch_id in self.check_vars:
                        self.check_vars[patch_id].set(is_enabled)
                self._refresh_avatar_table()
                self._setup_chapter_combo()
                self._setup_snrd_chapter_combo()

                messagebox.showinfo(
                    "还原成功",
                    f"已成功从备份恢复原版文件:\n{', '.join(restored)}"
                )
                self.lbl_status.configure(text=f"已从备份恢复原版: {', '.join(restored)}", foreground="#006600")
            except Exception as e:
                messagebox.showerror("还原失败", f"还原备份时出错:\n{e}")
