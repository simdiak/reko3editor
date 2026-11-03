"""
《三国志英杰传》战斗部队部署展开编辑器 (DeployArmyDialog)
参考 Web 前端架构，支持 30 位我军/敌军部队成员的坐标位置、兵种、等级、出场方式、AI 以及战场宏观设置的详细配置
"""

import copy
import struct
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from msave_editor.constants import AVATAR_NAMES, BINGZHONG_LIST, DAOJU_LIST, JUNTUAN_MAP
from prog_editor.snrd_manager import (
    ScriptInstruction,
    AI_TYPES,
    DIRECTIONS,
    FriendDeployment,
    FriendUnit,
    EnemyDeployment,
    EnemyUnit,
    parse_friend_deployment,
    serialize_friend_deployment,
    parse_enemy_deployment,
    serialize_enemy_deployment,
    get_avatar_name
)


class DeployArmyDialog(tk.Toplevel):
    """部队部署详细展开配置对话框 (支持 0x03 我军部署 与 0x22 敌军部署)"""

    def __init__(
        self,
        parent: tk.Widget,
        instruction: ScriptInstruction,
        on_applied: Callable[[], None]
    ):
        super().__init__(parent)
        self.instruction = instruction
        self.on_applied = on_applied
        self.opcode = instruction.opcode

        # 384 武将选项列表
        self.avatar_options = ["(未部署/空)"] + list(AVATAR_NAMES)
        self.direction_options = list(DIRECTIONS.values())
        self.bingzhong_options = list(BINGZHONG_LIST)
        self.ai_options = list(AI_TYPES.values())

        if self.opcode == 0x03:
            self.title("⚔ 部署我军部队阵容展开编辑器 (30人阵容 / 坐标位置 / 战斗回合 / 主将)")
            self.deploy_data: FriendDeployment = parse_friend_deployment(bytes(instruction.raw_bytes))
        else:
            self.title("🛡 部署敌军部队阵容展开编辑器 (30人阵容 / 兵种等级 / 坐标位置 / 战场AI)")
            self.deploy_data: EnemyDeployment = parse_enemy_deployment(bytes(instruction.raw_bytes))

        self.selected_slot_idx = 0
        self._updating_form = False

        self.geometry("1100x680")
        self.minsize(980, 560)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate_table()

    def _build_ui(self):
        # 1. 顶部设置栏
        if self.opcode == 0x03:
            self._build_friend_topbar()
        else:
            self._build_enemy_topbar()

        # 2. 底部确定与取消按钮栏（优先停靠底部，确保始终完全显示）
        bottom_bar = ttk.Frame(self, padding=(10, 8, 10, 8))
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        btn_confirm = ttk.Button(
            bottom_bar,
            text="✔ 确认",
            style="Primary.TButton",
            width=10,
            command=self._on_confirm
        )
        btn_confirm.pack(side=tk.RIGHT, padx=(8, 0))

        btn_cancel = ttk.Button(
            bottom_bar, text="✖ 取消", width=10, command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT)

        # 3. 中部主体（左侧表格 + 右侧槽位属性微调）
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=4)

        # 3.1 左侧 30 槽位表格
        table_frame = ttk.LabelFrame(paned, text=" 30 支部队部署席位一览表 ", padding=6)
        paned.add(table_frame, weight=3)

        self._build_table(table_frame)

        # 3.2 右侧单槽位详细参数配置
        self.slot_edit_frame = ttk.LabelFrame(paned, text=" 选定席位参数详细配置 ", padding=10)
        paned.add(self.slot_edit_frame, weight=2)

        if self.opcode == 0x03:
            self._build_friend_slot_form(self.slot_edit_frame)
        else:
            self._build_enemy_slot_form(self.slot_edit_frame)

        # 快捷键绑定
        self.bind("<Return>", lambda e: self._on_confirm())

    # ================= 顶部宏观设置 =================

    def _build_friend_topbar(self):
        frame = ttk.LabelFrame(self, text=" 战斗宏观规则与主将设定 ", padding=8)
        frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(6, 2))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)

        # 不可撤退
        ttk.Label(row, text="撤退规则:").pack(side=tk.LEFT, padx=(0, 2))
        self.f_retreat_var = tk.StringVar(
            value="1: 不可撤退" if self.deploy_data.not_retreat else "0: 可自由撤退"
        )
        cb_ret = ttk.Combobox(
            row, textvariable=self.f_retreat_var, values=["0: 可自由撤退", "1: 不可撤退"],
            state="readonly", width=11
        )
        cb_ret.pack(side=tk.LEFT, padx=(0, 8))

        # 回合数
        ttk.Label(row, text="限制回合:").pack(side=tk.LEFT, padx=(0, 2))
        self.f_rounds_var = tk.IntVar(value=self.deploy_data.round_cnt)
        sp_rounds = ttk.Spinbox(
            row, from_=1, to=100, textvariable=self.f_rounds_var, width=4
        )
        sp_rounds.pack(side=tk.LEFT, padx=(0, 8))

        # 继承回合数
        ttk.Label(row, text="继承回合:").pack(side=tk.LEFT, padx=(0, 2))
        self.f_inherit_var = tk.StringVar(
            value="1: 是" if self.deploy_data.round_inherit else "0: 否"
        )
        cb_inh = ttk.Combobox(
            row, textvariable=self.f_inherit_var, values=["0: 否", "1: 是"],
            state="readonly", width=5
        )
        cb_inh.pack(side=tk.LEFT, padx=(0, 8))

        # 敌方主将
        ttk.Label(row, text="敌将:").pack(side=tk.LEFT, padx=(0, 2))
        opp_name = get_avatar_name(self.deploy_data.opp_main)
        self.f_opp_main_var = tk.StringVar(value=opp_name)
        cb_opp = ttk.Combobox(
            row, textvariable=self.f_opp_main_var, values=self.avatar_options,
            state="readonly", width=10
        )
        cb_opp.pack(side=tk.LEFT, padx=(0, 8))

        # 我方主将
        ttk.Label(row, text="我将:").pack(side=tk.LEFT, padx=(0, 2))
        my_name = get_avatar_name(self.deploy_data.my_main)
        self.f_my_main_var = tk.StringVar(value=my_name)
        cb_my = ttk.Combobox(
            row, textvariable=self.f_my_main_var, values=list(AVATAR_NAMES),
            state="readonly", width=10
        )
        cb_my.pack(side=tk.LEFT, padx=(0, 10))

    def _build_enemy_topbar(self):
        frame = ttk.LabelFrame(self, text=" 敌方部队部署概览 ", padding=8)
        frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(6, 2))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)

        active_cnt = sum(1 for u in self.deploy_data.units if u.avatar_id != 0xFFFF)
        self.lbl_e_summary = ttk.Label(
            row,
            text=f"已配置敌军: {active_cnt} / 30 支  |  空槽位: {30 - active_cnt} 个",
            font=('Sans', 10, 'bold')
        )
        self.lbl_e_summary.pack(side=tk.LEFT, padx=(0, 15))

        btn_batch_add5 = ttk.Button(
            row, text="⚡ 全员Lv+5", width=9, command=lambda: self._batch_enemy_level(5)
        )
        btn_batch_add5.pack(side=tk.RIGHT, padx=2)

        btn_batch_sub5 = ttk.Button(
            row, text="⚡ 全员Lv-5", width=9, command=lambda: self._batch_enemy_level(-5)
        )
        btn_batch_sub5.pack(side=tk.RIGHT, padx=2)

    # ================= 30 席位表格构建 =================

    def _build_table(self, parent: ttk.Frame):
        if self.opcode == 0x03:
            cols = ("slot", "avatar", "pos", "appear", "event", "direct", "fubing")
            self.table = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
            self.table.heading("slot", text="席位")
            self.table.heading("avatar", text="武将")
            self.table.heading("pos", text="坐标 (X, Y)")
            self.table.heading("appear", text="出场方式")
            self.table.heading("event", text="关联事件")
            self.table.heading("direct", text="朝向")
            self.table.heading("fubing", text="伏兵")

            self.table.column("slot", width=55, anchor="center")
            self.table.column("avatar", width=100, anchor="w")
            self.table.column("pos", width=90, anchor="center")
            self.table.column("appear", width=85, anchor="center")
            self.table.column("event", width=75, anchor="center")
            self.table.column("direct", width=80, anchor="center")
            self.table.column("fubing", width=60, anchor="center")
        else:
            cols = ("slot", "avatar", "bz", "lv", "pos", "appear", "event", "direct", "fubing", "ai", "ai_target")
            self.table = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
            self.table.heading("slot", text="席位")
            self.table.heading("avatar", text="武将")
            self.table.heading("bz", text="兵种")
            self.table.heading("lv", text="等级")
            self.table.heading("pos", text="坐标(X,Y)")
            self.table.heading("appear", text="出场")
            self.table.heading("event", text="事件")
            self.table.heading("direct", text="朝向")
            self.table.heading("fubing", text="伏兵")
            self.table.heading("ai", text="AI模式")
            self.table.heading("ai_target", text="AI附加目标")

            self.table.column("slot", width=50, anchor="center")
            self.table.column("avatar", width=85, anchor="w")
            self.table.column("bz", width=75, anchor="center")
            self.table.column("lv", width=45, anchor="center")
            self.table.column("pos", width=75, anchor="center")
            self.table.column("appear", width=70, anchor="center")
            self.table.column("event", width=55, anchor="center")
            self.table.column("direct", width=65, anchor="center")
            self.table.column("fubing", width=50, anchor="center")
            self.table.column("ai", width=110, anchor="w")
            self.table.column("ai_target", width=95, anchor="w")

        v_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=v_scroll.set)

        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.table.bind("<<TreeviewSelect>>", self._on_table_select)

    def _populate_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

        if self.opcode == 0x03:
            for i, u in enumerate(self.deploy_data.units):
                name = get_avatar_name(u.avatar_id)
                pos = f"({u.x}, {u.y})" if u.avatar_id != 0xFFFF else "-"
                app = "直接出场" if u.appear == 0 else "事件出场"
                ev = f"标志{u.event}" if u.appear == 1 else "-"
                d = DIRECTIONS.get(u.direction, str(u.direction))
                fu = "伏兵" if u.fubing == 1 else "否"

                self.table.insert(
                    "", tk.END, iid=str(i),
                    values=(f"第 {i+1} 席", name, pos, app, ev, d, fu)
                )
        else:
            for i, u in enumerate(self.deploy_data.units):
                name = get_avatar_name(u.avatar_id)
                bz = BINGZHONG_LIST[u.bingzhong] if u.bingzhong < len(BINGZHONG_LIST) else f"0x{u.bingzhong:02X}"
                lv = f"Lv{u.level}" if u.avatar_id != 0xFFFF else "-"
                pos = f"({u.x}, {u.y})" if u.avatar_id != 0xFFFF else "-"
                app = "直接" if u.appear == 0 else "事件"
                ev = str(u.event) if u.appear == 1 else "-"
                d = DIRECTIONS.get(u.direction, str(u.direction))
                fu = "是" if u.fubing == 1 else "否"
                ai_str = AI_TYPES.get(u.ai_type, f"AI {u.ai_type}")

                if u.ai_type in (4, 6):
                    target_str = f"({u.ai_param1}, {u.ai_param2})"
                elif u.ai_type in (3, 5):
                    target_aid = u.ai_param1 + (u.ai_param2 << 8)
                    target_str = f"[{get_avatar_name(target_aid)}]"
                else:
                    target_str = "-"

                self.table.insert(
                    "", tk.END, iid=str(i),
                    values=(f"第 {i+1} 席", name, bz, lv, pos, app, ev, d, fu, ai_str, target_str)
                )

        # 默认选中第 0 席位
        self.table.selection_set("0")
        self._load_slot_into_form(0)

    def _on_table_select(self, event=None):
        sel = self.table.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.selected_slot_idx = idx
        self._load_slot_into_form(idx)

    # ================= 右侧表单：0x03 我军槽位 =================

    def _build_friend_slot_form(self, parent: ttk.LabelFrame):
        self.f_title_lbl = ttk.Label(parent, text="当前编辑: 第 1 席位", font=('Sans', 10, 'bold'))
        self.f_title_lbl.pack(anchor="w", pady=(0, 6))

        grid = ttk.Frame(parent)
        grid.pack(fill=tk.X, pady=(0, 6))

        # Row 0: 登场武将
        ttk.Label(grid, text="登场武将:").grid(row=0, column=0, sticky="w", padx=2, pady=3)
        self.slot_f_avatar_var = tk.StringVar()
        self.slot_f_avatar_combo = ttk.Combobox(
            grid, textvariable=self.slot_f_avatar_var, values=self.avatar_options,
            state="readonly", width=14
        )
        self.slot_f_avatar_combo.grid(row=0, column=1, columnspan=3, sticky="w", padx=2, pady=3)
        self.slot_f_avatar_combo.bind("<<ComboboxSelected>>", self._on_friend_slot_changed)

        # Row 1: X 坐标 & Y 坐标
        ttk.Label(grid, text="坐标 X:").grid(row=1, column=0, sticky="w", padx=2, pady=3)
        self.slot_f_x_var = tk.IntVar(value=0)
        sp_x = ttk.Spinbox(
            grid, from_=0, to=99, textvariable=self.slot_f_x_var, width=5,
            command=self._on_friend_slot_changed
        )
        sp_x.grid(row=1, column=1, sticky="w", padx=2, pady=3)
        sp_x.bind("<KeyRelease>", self._on_friend_slot_changed)

        ttk.Label(grid, text="坐标 Y:").grid(row=1, column=2, sticky="w", padx=4, pady=3)
        self.slot_f_y_var = tk.IntVar(value=0)
        sp_y = ttk.Spinbox(
            grid, from_=0, to=99, textvariable=self.slot_f_y_var, width=5,
            command=self._on_friend_slot_changed
        )
        sp_y.grid(row=1, column=3, sticky="w", padx=2, pady=3)
        sp_y.bind("<KeyRelease>", self._on_friend_slot_changed)

        # Row 2: 出场方式 & 关联事件
        ttk.Label(grid, text="出场模式:").grid(row=2, column=0, sticky="w", padx=2, pady=3)
        self.slot_f_appear_var = tk.StringVar(value="0: 直接出场")
        cb_app = ttk.Combobox(
            grid, textvariable=self.slot_f_appear_var,
            values=["0: 直接出场", "1: 事件触发后出场"],
            state="readonly", width=11
        )
        cb_app.grid(row=2, column=1, sticky="w", padx=2, pady=3)
        cb_app.bind("<<ComboboxSelected>>", self._on_friend_slot_changed)

        ttk.Label(grid, text="事件Flag:").grid(row=2, column=2, sticky="w", padx=4, pady=3)
        self.slot_f_event_var = tk.IntVar(value=0)
        sp_ev = ttk.Spinbox(
            grid, from_=0, to=255, textvariable=self.slot_f_event_var, width=5,
            command=self._on_friend_slot_changed
        )
        sp_ev.grid(row=2, column=3, sticky="w", padx=2, pady=3)
        sp_ev.bind("<KeyRelease>", self._on_friend_slot_changed)

        # Row 3: 朝向 & 伏兵
        ttk.Label(grid, text="初始朝向:").grid(row=3, column=0, sticky="w", padx=2, pady=3)
        self.slot_f_direct_var = tk.StringVar(value=DIRECTIONS[0])
        cb_d = ttk.Combobox(
            grid, textvariable=self.slot_f_direct_var, values=self.direction_options,
            state="readonly", width=11
        )
        cb_d.grid(row=3, column=1, sticky="w", padx=2, pady=3)
        cb_d.bind("<<ComboboxSelected>>", self._on_friend_slot_changed)

        ttk.Label(grid, text="部队状态:").grid(row=3, column=2, sticky="w", padx=4, pady=3)
        self.slot_f_fubing_var = tk.StringVar(value="0: 正常部队")
        cb_fu = ttk.Combobox(
            grid, textvariable=self.slot_f_fubing_var,
            values=["0: 正常部队", "1: 伏兵 (隐藏状态)"],
            state="readonly", width=11
        )
        cb_fu.grid(row=3, column=3, sticky="w", padx=2, pady=3)
        cb_fu.bind("<<ComboboxSelected>>", self._on_friend_slot_changed)

        # 快捷操作按钮
        btn_box = ttk.LabelFrame(parent, text=" 快捷席位设定 ", padding=6)
        btn_box.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(
            btn_box, text="清空本席位 (设为未部署)", command=self._clear_current_friend_slot
        ).pack(fill=tk.X, pady=2)

        quick_row1 = ttk.Frame(btn_box)
        quick_row1.pack(fill=tk.X, pady=2)
        ttk.Button(
            quick_row1, text="设为刘备", width=8, command=lambda: self._set_quick_avatar("劉備")
        ).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        ttk.Button(
            quick_row1, text="设为关羽", width=8, command=lambda: self._set_quick_avatar("關羽")
        ).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        ttk.Button(
            quick_row1, text="设为张飞", width=8, command=lambda: self._set_quick_avatar("張飛")
        ).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)

        quick_row2 = ttk.Frame(btn_box)
        quick_row2.pack(fill=tk.X, pady=2)
        ttk.Button(
            quick_row2, text="设为赵云", width=8, command=lambda: self._set_quick_avatar("趙雲")
        ).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        ttk.Button(
            quick_row2, text="设为诸葛亮", width=8, command=lambda: self._set_quick_avatar("諸葛亮")
        ).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)

    # ================= 右侧表单：0x22 敌军槽位 =================

    def _build_enemy_slot_form(self, parent: ttk.LabelFrame):
        self.e_title_lbl = ttk.Label(parent, text="当前编辑: 第 1 席位", font=('Sans', 10, 'bold'))
        self.e_title_lbl.pack(anchor="w", pady=(0, 6))

        grid = ttk.Frame(parent)
        grid.pack(fill=tk.X, pady=(0, 6))

        # Row 0: 角色 & 兵种
        ttk.Label(grid, text="登场武将:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.slot_e_avatar_var = tk.StringVar()
        self.slot_e_avatar_combo = ttk.Combobox(
            grid, textvariable=self.slot_e_avatar_var, values=self.avatar_options,
            state="readonly", width=11
        )
        self.slot_e_avatar_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.slot_e_avatar_combo.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        ttk.Label(grid, text="兵种设定:").grid(row=0, column=2, sticky="w", padx=4, pady=2)
        self.slot_e_bz_var = tk.StringVar(value=BINGZHONG_LIST[0])
        self.slot_e_bz_combo = ttk.Combobox(
            grid, textvariable=self.slot_e_bz_var, values=self.bingzhong_options,
            state="readonly", width=10
        )
        self.slot_e_bz_combo.grid(row=0, column=3, sticky="w", padx=2, pady=2)
        self.slot_e_bz_combo.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        # Row 1: 等级 & 朝向
        ttk.Label(grid, text="部队等级:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.slot_e_lv_var = tk.IntVar(value=1)
        sp_lv = ttk.Spinbox(
            grid, from_=1, to=99, textvariable=self.slot_e_lv_var, width=5,
            command=self._on_enemy_slot_changed
        )
        sp_lv.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        sp_lv.bind("<KeyRelease>", self._on_enemy_slot_changed)

        ttk.Label(grid, text="初始朝向:").grid(row=1, column=2, sticky="w", padx=4, pady=2)
        self.slot_e_direct_var = tk.StringVar(value=DIRECTIONS[0])
        cb_d = ttk.Combobox(
            grid, textvariable=self.slot_e_direct_var, values=self.direction_options,
            state="readonly", width=10
        )
        cb_d.grid(row=1, column=3, sticky="w", padx=2, pady=2)
        cb_d.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        # Row 2: X 坐标 & Y 坐标
        ttk.Label(grid, text="坐标 X:").grid(row=2, column=0, sticky="w", padx=2, pady=2)
        self.slot_e_x_var = tk.IntVar(value=0)
        sp_x = ttk.Spinbox(
            grid, from_=0, to=99, textvariable=self.slot_e_x_var, width=5,
            command=self._on_enemy_slot_changed
        )
        sp_x.grid(row=2, column=1, sticky="w", padx=2, pady=2)
        sp_x.bind("<KeyRelease>", self._on_enemy_slot_changed)

        ttk.Label(grid, text="坐标 Y:").grid(row=2, column=2, sticky="w", padx=4, pady=2)
        self.slot_e_y_var = tk.IntVar(value=0)
        sp_y = ttk.Spinbox(
            grid, from_=0, to=99, textvariable=self.slot_e_y_var, width=5,
            command=self._on_enemy_slot_changed
        )
        sp_y.grid(row=2, column=3, sticky="w", padx=2, pady=2)
        sp_y.bind("<KeyRelease>", self._on_enemy_slot_changed)

        # Row 3: 出场模式 & 关联事件
        ttk.Label(grid, text="出场模式:").grid(row=3, column=0, sticky="w", padx=2, pady=2)
        self.slot_e_appear_var = tk.StringVar(value="0: 直接出场")
        cb_app = ttk.Combobox(
            grid, textvariable=self.slot_e_appear_var,
            values=["0: 直接出场", "1: 事件触发后出场"],
            state="readonly", width=11
        )
        cb_app.grid(row=3, column=1, sticky="w", padx=2, pady=2)
        cb_app.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        ttk.Label(grid, text="事件Flag:").grid(row=3, column=2, sticky="w", padx=4, pady=2)
        self.slot_e_event_var = tk.IntVar(value=0)
        sp_ev = ttk.Spinbox(
            grid, from_=0, to=255, textvariable=self.slot_e_event_var, width=5,
            command=self._on_enemy_slot_changed
        )
        sp_ev.grid(row=3, column=3, sticky="w", padx=2, pady=2)
        sp_ev.bind("<KeyRelease>", self._on_enemy_slot_changed)

        # Row 4: 伏兵 & 战场AI
        ttk.Label(grid, text="部队状态:").grid(row=4, column=0, sticky="w", padx=2, pady=2)
        self.slot_e_fubing_var = tk.StringVar(value="0: 正常部队")
        cb_fu = ttk.Combobox(
            grid, textvariable=self.slot_e_fubing_var,
            values=["0: 正常部队", "1: 伏兵 (隐藏状态)"],
            state="readonly", width=11
        )
        cb_fu.grid(row=4, column=1, sticky="w", padx=2, pady=2)
        cb_fu.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        ttk.Label(grid, text="战场 AI:").grid(row=4, column=2, sticky="w", padx=4, pady=2)
        self.slot_e_ai_var = tk.StringVar(value=AI_TYPES[0])
        cb_ai = ttk.Combobox(
            grid, textvariable=self.slot_e_ai_var, values=self.ai_options,
            state="readonly", width=10
        )
        cb_ai.grid(row=4, column=3, sticky="w", padx=2, pady=2)
        cb_ai.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        # AI 附加目标动态区域
        self.ai_target_container = ttk.Frame(parent)
        self.ai_target_container.pack(fill=tk.X, pady=(2, 6))

        # 目标坐标 (X, Y)
        self.ai_pos_frame = ttk.Frame(self.ai_target_container)
        ttk.Label(self.ai_pos_frame, text="AI目标X:").pack(side=tk.LEFT, padx=(0, 2))
        self.ai_target_x_var = tk.IntVar(value=0)
        sp_tx = ttk.Spinbox(
            self.ai_pos_frame, from_=0, to=99, textvariable=self.ai_target_x_var, width=4,
            command=self._on_enemy_slot_changed
        )
        sp_tx.pack(side=tk.LEFT, padx=(0, 6))
        sp_tx.bind("<KeyRelease>", self._on_enemy_slot_changed)

        ttk.Label(self.ai_pos_frame, text="Y:").pack(side=tk.LEFT, padx=(0, 2))
        self.ai_target_y_var = tk.IntVar(value=0)
        sp_ty = ttk.Spinbox(
            self.ai_pos_frame, from_=0, to=99, textvariable=self.ai_target_y_var, width=4,
            command=self._on_enemy_slot_changed
        )
        sp_ty.pack(side=tk.LEFT)
        sp_ty.bind("<KeyRelease>", self._on_enemy_slot_changed)

        # 目标武将 (仇人)
        self.ai_avatar_frame = ttk.Frame(self.ai_target_container)
        ttk.Label(self.ai_avatar_frame, text="攻击仇人武将:").pack(side=tk.LEFT, padx=(0, 2))
        self.ai_target_avatar_var = tk.StringVar()
        self.cb_ai_avatar = ttk.Combobox(
            self.ai_avatar_frame, textvariable=self.ai_target_avatar_var,
            values=list(AVATAR_NAMES), state="readonly", width=12
        )
        self.cb_ai_avatar.pack(side=tk.LEFT)
        self.cb_ai_avatar.bind("<<ComboboxSelected>>", self._on_enemy_slot_changed)

        # 无附加目标说明
        self.lbl_ai_none = ttk.Label(
            self.ai_target_container, text="当前 AI 模式无须附加目标", foreground="#777777"
        )

        # 快捷按钮
        btn_box = ttk.LabelFrame(parent, text=" 快捷席位设定 ", padding=6)
        btn_box.pack(fill=tk.X, pady=(6, 0))

        btn_row_ops = ttk.Frame(btn_box)
        btn_row_ops.pack(fill=tk.X, pady=2)

        ttk.Button(
            btn_row_ops, text="清空本席位", command=self._clear_current_enemy_slot
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Button(
            btn_row_ops, text="当前Lv+5", width=9, command=lambda: self._add_current_enemy_level(5)
        ).pack(side=tk.LEFT, padx=1)

        ttk.Button(
            btn_row_ops, text="当前Lv-5", width=9, command=lambda: self._add_current_enemy_level(-5)
        ).pack(side=tk.LEFT, padx=1)

    # ================= 状态装载与表单同步 =================

    def _load_slot_into_form(self, idx: int):
        self._updating_form = True

        if self.opcode == 0x03:
            u = self.deploy_data.units[idx]
            self.f_title_lbl.configure(text=f"当前编辑: 第 {idx + 1} 席位 ({get_avatar_name(u.avatar_id)})")

            name = get_avatar_name(u.avatar_id)
            self.slot_f_avatar_var.set(name)
            self.slot_f_x_var.set(u.x)
            self.slot_f_y_var.set(u.y)
            self.slot_f_appear_var.set("1: 事件触发后出场" if u.appear == 1 else "0: 直接出场")
            self.slot_f_event_var.set(u.event)
            self.slot_f_direct_var.set(DIRECTIONS.get(u.direction, DIRECTIONS[0]))
            self.slot_f_fubing_var.set("1: 伏兵 (隐藏状态)" if u.fubing == 1 else "0: 正常部队")

        else:
            u = self.deploy_data.units[idx]
            self.e_title_lbl.configure(text=f"当前编辑: 第 {idx + 1} 席位 ({get_avatar_name(u.avatar_id)})")

            name = get_avatar_name(u.avatar_id)
            self.slot_e_avatar_var.set(name)
            bz = BINGZHONG_LIST[u.bingzhong] if u.bingzhong < len(BINGZHONG_LIST) else BINGZHONG_LIST[0]
            self.slot_e_bz_var.set(bz)
            self.slot_e_lv_var.set(u.level)
            self.slot_e_x_var.set(u.x)
            self.slot_e_y_var.set(u.y)
            self.slot_e_appear_var.set("1: 事件触发后出场" if u.appear == 1 else "0: 直接出场")
            self.slot_e_event_var.set(u.event)
            self.slot_e_direct_var.set(DIRECTIONS.get(u.direction, DIRECTIONS[0]))
            self.slot_e_fubing_var.set("1: 伏兵 (隐藏状态)" if u.fubing == 1 else "0: 正常部队")
            self.slot_e_ai_var.set(AI_TYPES.get(u.ai_type, AI_TYPES[0]))

            self._update_ai_target_controls(u.ai_type, u.ai_param1, u.ai_param2)

        self._updating_form = False

    def _update_ai_target_controls(self, ai_type: int, p1: int, p2: int):
        self.ai_pos_frame.pack_forget()
        self.ai_avatar_frame.pack_forget()
        self.lbl_ai_none.pack_forget()

        if ai_type in (4, 6):
            self.ai_target_x_var.set(p1)
            self.ai_target_y_var.set(p2)
            self.ai_pos_frame.pack(fill=tk.X, pady=2)
        elif ai_type in (3, 5):
            target_aid = p1 + (p2 << 8)
            target_name = get_avatar_name(target_aid)
            if target_name in AVATAR_NAMES:
                self.ai_target_avatar_var.set(target_name)
            else:
                self.ai_target_avatar_var.set(AVATAR_NAMES[0])
            self.ai_avatar_frame.pack(fill=tk.X, pady=2)
        else:
            self.lbl_ai_none.pack(anchor="w", pady=2)

    # ================= 属性变动回调与表格刷新 =================

    def _on_friend_slot_changed(self, event=None):
        if self._updating_form:
            return
        idx = self.selected_slot_idx
        u = self.deploy_data.units[idx]

        # 解析角色
        name = self.slot_f_avatar_var.get()
        if name in AVATAR_NAMES:
            u.avatar_id = AVATAR_NAMES.index(name)
        else:
            u.avatar_id = 0xFFFF

        try:
            u.x = int(self.slot_f_x_var.get())
            u.y = int(self.slot_f_y_var.get())
        except (ValueError, tk.TclError):
            pass

        u.appear = 1 if "1:" in self.slot_f_appear_var.get() else 0
        try:
            u.event = int(self.slot_f_event_var.get())
        except (ValueError, tk.TclError):
            pass

        d_name = self.slot_f_direct_var.get()
        for k, v in DIRECTIONS.items():
            if v == d_name:
                u.direction = k
                break

        u.fubing = 1 if "1:" in self.slot_f_fubing_var.get() else 0

        # 更新表格行
        name_str = get_avatar_name(u.avatar_id)
        pos_str = f"({u.x}, {u.y})" if u.avatar_id != 0xFFFF else "-"
        app_str = "直接出场" if u.appear == 0 else "事件出场"
        ev_str = f"标志{u.event}" if u.appear == 1 else "-"
        d_str = DIRECTIONS.get(u.direction, str(u.direction))
        fu_str = "伏兵" if u.fubing == 1 else "否"

        self.table.item(
            str(idx),
            values=(f"第 {idx+1} 席", name_str, pos_str, app_str, ev_str, d_str, fu_str)
        )
        self.f_title_lbl.configure(text=f"当前编辑: 第 {idx + 1} 席位 ({name_str})")

    def _on_enemy_slot_changed(self, event=None):
        if self._updating_form:
            return
        idx = self.selected_slot_idx
        u = self.deploy_data.units[idx]

        # 角色
        name = self.slot_e_avatar_var.get()
        if name in AVATAR_NAMES:
            u.avatar_id = AVATAR_NAMES.index(name)
        else:
            u.avatar_id = 0xFFFF

        # 兵种
        bz_name = self.slot_e_bz_var.get()
        if bz_name in BINGZHONG_LIST:
            u.bingzhong = BINGZHONG_LIST.index(bz_name)

        try:
            u.level = max(1, min(99, int(self.slot_e_lv_var.get())))
            u.x = int(self.slot_e_x_var.get())
            u.y = int(self.slot_e_y_var.get())
        except (ValueError, tk.TclError):
            pass

        u.appear = 1 if "1:" in self.slot_e_appear_var.get() else 0
        try:
            u.event = int(self.slot_e_event_var.get())
        except (ValueError, tk.TclError):
            pass

        d_name = self.slot_e_direct_var.get()
        for k, v in DIRECTIONS.items():
            if v == d_name:
                u.direction = k
                break

        u.fubing = 1 if "1:" in self.slot_e_fubing_var.get() else 0

        # AI
        ai_name = self.slot_e_ai_var.get()
        for k, v in AI_TYPES.items():
            if v == ai_name:
                u.ai_type = k
                break

        if u.ai_type in (4, 6):
            try:
                u.ai_param1 = int(self.ai_target_x_var.get())
                u.ai_param2 = int(self.ai_target_y_var.get())
            except (ValueError, tk.TclError):
                pass
        elif u.ai_type in (3, 5):
            t_name = self.ai_target_avatar_var.get()
            if t_name in AVATAR_NAMES:
                t_aid = AVATAR_NAMES.index(t_name)
                u.ai_param1 = t_aid & 0xFF
                u.ai_param2 = (t_aid >> 8) & 0xFF
        else:
            u.ai_param1 = 0
            u.ai_param2 = 0

        self._update_ai_target_controls(u.ai_type, u.ai_param1, u.ai_param2)

        # 更新表格行
        name_str = get_avatar_name(u.avatar_id)
        bz_str = BINGZHONG_LIST[u.bingzhong] if u.bingzhong < len(BINGZHONG_LIST) else f"0x{u.bingzhong:02X}"
        lv_str = f"Lv{u.level}" if u.avatar_id != 0xFFFF else "-"
        pos_str = f"({u.x}, {u.y})" if u.avatar_id != 0xFFFF else "-"
        app_str = "直接" if u.appear == 0 else "事件"
        ev_str = str(u.event) if u.appear == 1 else "-"
        d_str = DIRECTIONS.get(u.direction, str(u.direction))
        fu_str = "是" if u.fubing == 1 else "否"
        ai_str = AI_TYPES.get(u.ai_type, f"AI {u.ai_type}")

        if u.ai_type in (4, 6):
            target_str = f"({u.ai_param1}, {u.ai_param2})"
        elif u.ai_type in (3, 5):
            target_aid = u.ai_param1 + (u.ai_param2 << 8)
            target_str = f"[{get_avatar_name(target_aid)}]"
        else:
            target_str = "-"

        self.table.item(
            str(idx),
            values=(f"第 {idx+1} 席", name_str, bz_str, lv_str, pos_str, app_str, ev_str, d_str, fu_str, ai_str, target_str)
        )
        self.e_title_lbl.configure(text=f"当前编辑: 第 {idx + 1} 席位 ({name_str})")

        active_cnt = sum(1 for item in self.deploy_data.units if item.avatar_id != 0xFFFF)
        self.lbl_e_summary.configure(text=f"已配置敌军部队: {active_cnt} / 30 支  |  空余槽位: {30 - active_cnt} 个")

    # ================= 快捷操作 =================

    def _clear_current_friend_slot(self):
        self.slot_f_avatar_var.set("(未部署/空)")
        self.slot_f_x_var.set(0)
        self.slot_f_y_var.set(0)
        self._on_friend_slot_changed()

    def _set_quick_avatar(self, avatar_name: str):
        if avatar_name in AVATAR_NAMES:
            self.slot_f_avatar_var.set(avatar_name)
            self._on_friend_slot_changed()

    def _clear_current_enemy_slot(self):
        self.slot_e_avatar_var.set("(未部署/空)")
        self.slot_e_x_var.set(0)
        self.slot_e_y_var.set(0)
        self._on_enemy_slot_changed()

    def _add_current_enemy_level(self, delta: int):
        cur = self.slot_e_lv_var.get()
        new_lv = max(1, min(99, cur + delta))
        self.slot_e_lv_var.set(new_lv)
        self._on_enemy_slot_changed()

    def _batch_enemy_level(self, delta: int):
        for u in self.deploy_data.units:
            if u.avatar_id != 0xFFFF:
                u.level = max(1, min(99, u.level + delta))
        self._populate_table()

    # ================= 确认应用 =================

    def _on_confirm(self):
        if self.opcode == 0x03:
            # 读取宏观设置
            self.deploy_data.not_retreat = 1 if "1:" in self.f_retreat_var.get() else 0
            try:
                self.deploy_data.round_cnt = max(1, min(100, int(self.f_rounds_var.get())))
            except (ValueError, tk.TclError):
                pass
            self.deploy_data.round_inherit = 1 if "1:" in self.f_inherit_var.get() else 0

            opp_name = self.f_opp_main_var.get()
            if opp_name in AVATAR_NAMES:
                self.deploy_data.opp_main = AVATAR_NAMES.index(opp_name)
            else:
                self.deploy_data.opp_main = 0xFFFF

            my_name = self.f_my_main_var.get()
            if my_name in AVATAR_NAMES:
                self.deploy_data.my_main = AVATAR_NAMES.index(my_name)
            else:
                self.deploy_data.my_main = 0x0000

            new_bytes = serialize_friend_deployment(self.deploy_data)
            self.instruction.raw_bytes = bytearray(new_bytes)

        else:
            new_bytes = serialize_enemy_deployment(self.deploy_data)
            self.instruction.raw_bytes = bytearray(new_bytes)

        if self.on_applied:
            self.on_applied()

        self.destroy()

