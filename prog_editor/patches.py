"""
《三国志英杰传》主程序 (Main.exe) 补丁定义表
包含所有经典经过验证的二进制修改项
"""

from typing import List, Tuple


class Patch:
    """单个主程序功能补丁"""

    def __init__(
        self,
        patch_id: str,
        name: str,
        category: str,
        description: str,
        diffs: List[Tuple[int, bytes, bytes]]
    ):
        self.patch_id = patch_id
        self.name = name
        self.category = category
        self.description = description
        self.diffs = diffs  # [(offset, orig_bytes, patch_bytes), ...]

    def is_enabled(self, data: bytes) -> bool:
        """检查当前二进制数据中是否已启用该补丁"""
        for offset, _, patch_bytes in self.diffs:
            if data[offset : offset + len(patch_bytes)] != patch_bytes:
                return False
        return True

    def is_original(self, data: bytes) -> bool:
        """检查当前二进制数据中是否为原版字节"""
        for offset, orig_bytes, _ in self.diffs:
            if data[offset : offset + len(orig_bytes)] != orig_bytes:
                return False
        return True

    def apply(self, data: bytearray):
        """将补丁写入二进制数据缓冲区"""
        for offset, _, patch_bytes in self.diffs:
            data[offset : offset + len(patch_bytes)] = patch_bytes

    def revert(self, data: bytearray):
        """将数据缓冲区还原为原版字节"""
        for offset, orig_bytes, _ in self.diffs:
            data[offset : offset + len(orig_bytes)] = orig_bytes


# 经过数十年玩家社区与逆向工程验证的核心补丁列表
ALL_PATCHES: List[Patch] = [
    Patch(
        patch_id="debug_menu",
        name="开启官方隐藏战斗 DEBUG 菜单",
        category="开发者上帝模式",
        description="解锁光荣官方在战斗中预留的隐藏调试菜单。在战场右键菜单‘游戏结束’下方会出现‘DEBUG’选项，提供：随意移动、控制所有人(含敌军)、控制友军、立即胜利、全军等级+5、AI挂机托管等7大按需调用的调试能力！",
        diffs=[
            (0x026590, b"\xa2\x08\x2d", b"\x90\x90\x90"),  # 禁止初始化时清空 DEBUG 标志
            (0x039ED8, b"\x00", b"\x02"),                  # 激活 DEBUG 状态标志位
        ]
    ),
    Patch(
        patch_id="unlimited_move_control_enemy",
        name="全军无限制移动并可控制敌军",
        category="开发者上帝模式",
        description="硬编码绕过移动力与阵营判定。战斗中所有己方与敌方单位均无视移动范围，可自由瞬移到地图任意格子，且玩家可以直接操控敌方单位行动。",
        diffs=[
            (0x030545, b"\x74", b"\xeb")  # JZ -> JMP
        ]
    ),
    Patch(
        patch_id="unlimited_sp",
        name="策略值无消耗 (SP 不减)",
        category="战斗与策略优化",
        description="施放任何策略（如火计、落石、水计、施疗、鼓舞等）均不消耗任何策略值(SP)，再也不必为缺蓝烦恼。",
        diffs=[
            (0x02E3C3, b"\x28\x47\x0d", b"\x90\x90\x90")  # NOP 扣除 SP 的指令
        ]
    ),
    Patch(
        patch_id="strategy_always_hit",
        name="攻击性策略 100% 成功",
        category="战斗与策略优化",
        description="攻击类策略命中率强制判定为最高，所有落石、火计、水攻、混乱计等不再出现‘失败’或被敌方识破。",
        diffs=[
            (0x030D90, b"\x77\x05", b"\xeb\x05")  # JA -> JMP
        ]
    ),
    Patch(
        patch_id="heal_at_full_hp",
        name="兵力全满时仍可使用补给策略",
        category="练级便利辅助",
        description="原版满血时无法对友军使用豆、麦、施疗等加血策略。开启后满兵力也能施放补给，方便军师和部队随时随地练级刷经验。",
        diffs=[
            (0x02CD67, b"\x74\x38", b"\x90\x90")  # JZ -> NOP
        ]
    ),
    Patch(
        patch_id="inspire_at_full_morale",
        name="士气 100 时仍可使用激励策略",
        category="练级便利辅助",
        description="原版士气达到 100 后无法再施放激励/鼓舞。开启后满士气也可继续激励，是练级控刷经验的绝佳利器。",
        diffs=[
            (0x02CD73, b"\x75\x0e", b"\xeb\x0e")  # JNZ -> JMP
        ]
    ),
    Patch(
        patch_id="no_retreat_zero_morale",
        name="士气为 0 仍不溃退逃跑",
        category="战斗与策略优化",
        description="部队士气归零时不会被强制判定为溃败撤退，保留残存战力继续作战。",
        diffs=[
            (0x02CC13, b"\x75\x18", b"\xeb\x18")  # JNZ -> JMP
        ]
    ),
    Patch(
        patch_id="immune_confusion_low_morale",
        name="士气低于 30 仍不混乱",
        category="战斗与策略优化",
        description="原版部队士气跌破 30 会陷入混乱无法动弹。开启后免疫低士气带来的混乱状态，保持清醒行动。",
        diffs=[
            (0x02B4D2, b"\x73\x2e", b"\xeb\x2e")  # JAE -> JMP
        ]
    ),
    Patch(
        patch_id="bandit_counter_attack",
        name="贼兵受到攻击必定反击",
        category="趣味战斗平衡",
        description="山贼/恶贼/义贼受到敌方物理近战攻击时必定反击对手（原版有概率判定）。",
        diffs=[
            (0x030FBC, b"\x76\x04", b"\x90\x90")  # JBE -> NOP
        ]
    ),
    Patch(
        patch_id="military_band_fast_regen",
        name="军乐队列队补蓝加速 (每5级+1)",
        category="练级便利辅助",
        description="军乐队恢复邻近友军 SP 的数值提速：由原版的每 10 级恢复量 +1 提升为每 5 级恢复量 +1。",
        diffs=[
            (0x02A966, b"\xb1\x0a", b"\xb1\x05")  # MOV CL, 10 -> MOV CL, 5
        ]
    ),
    Patch(
        patch_id="always_sunny",
        name="战场天气锁定为晴天",
        category="趣味战斗平衡",
        description="每回合战场天气强制锁定为晴朗天气，雨雪天气计策受限的情况不再发生，火计随时可用。",
        diffs=[
            (0x02779B, b"\x3a\x46\xfe\x76\x05", b"\xb0\x00\x90\xeb\x2b")  # 强制写入天气代码 0
        ]
    )
]

