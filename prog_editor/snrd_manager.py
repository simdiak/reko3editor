"""
《三国志英杰传》剧本指令 (SNRD) 解析与回写管理模块
负责解析各章节 (Snr0d.r3 ~ Snr4d.r3) 的战斗部署、触发器条件、单挑、AI改变及事件开关指令
"""

import os
import shutil
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from msave_editor.constants import AVATAR_NAMES, BINGZHONG_LIST, DAOJU_LIST, JUNTUAN_MAP

TRIGGER_DESCR = {
    0x00: '顺序执行',
    0x01: '分支执行',
    0x02: '进入城市建筑',
    0x03: '对话',
    0x04: '单挑',
    0x05: '进入城市',
    0x06: '战场移到点',
    0x07: '战斗胜利',
    0x08: '战斗失败',
    0x09: '指定回合',
    0x0A: '未知条件',
    0x0B: '战场移到区域',
    0x0C: '撤退',
}

AI_TYPES = {
    0x00: '原地警戒(攻击)',
    0x01: '主动出击',
    0x02: '原地待命',
    0x03: '主动攻击仇人',
    0x04: '移动到坐标(攻击)',
    0x05: '协同作战/消灭目标',
    0x06: '移动到坐标(不攻击)',
    0x07: '未知AI',
}

DIRECTIONS = {
    0: '下 (南)',
    1: '左 (西)',
    2: '上 (北)',
    3: '右 (东)',
}

CODE_STEPS = {
    0x00: {'plen': 2, 'descr': '显示对话'},
    0x01: {'plen': 5, 'descr': '指定人物行动'},
    0x02: {'plen': 1, 'descr': '未知指令02'},
    0x03: {'plen': 281, 'descr': '部署我军部队'},
    0x04: {'plen': 0, 'descr': '未知指令04'},
    0x05: {'plen': 0, 'descr': '显示当前场景'},
    0x06: {'plen': 0, 'descr': '未知指令06'},
    0x07: {'plen': 2, 'descr': '显示图片'},
    0x08: {'plen': 2, 'descr': '中央显示信息'},
    0x09: {'plen': 2, 'descr': '指定战场/大地图'},
    0x0A: {'plen': 5, 'descr': '部署非战斗人物'},
    0x0B: {'plen': 2, 'descr': '画面中心信息'},
    0x0C: {'plen': 4, 'descr': '未知指令0C'},
    0x0D: {'plen': 2, 'descr': '左下角提示'},
    0x0E: {'plen': 2, 'descr': '中央提示'},
    0x0F: {'plen': 1, 'descr': '重新读入段指令'},
    0x10: {'plen': 4, 'descr': '武将单挑'},
    0x11: {'plen': 2, 'descr': '切换到地图/战场'},
    0x12: {'plen': 0, 'descr': '本章结束'},
    0x13: {'plen': 0, 'descr': '段指令强制结束'},
    0x14: {'plen': 2, 'descr': '设置事件开关'},
    0x15: {'plen': 2, 'descr': '出战对话框显示'},
    0x16: {'plen': 4, 'descr': '未知指令16'},
    0x17: {'plen': 1, 'descr': '剧情模式开关'},
    0x18: {'plen': 2, 'descr': '人物消失/撤退'},
    0x19: {'plen': 0, 'descr': '未知指令19'},
    0x1A: {'plen': 2, 'descr': '援军出现'},
    0x1B: {'plen': 1, 'descr': '获得道具'},
    0x1C: {'plen': 5, 'descr': '改变人物AI'},
    0x1D: {'plen': 4, 'descr': '未知指令1D'},
    0x1E: {'plen': 0, 'descr': '未知指令1E'},
    0x1F: {'plen': 0, 'descr': '未知指令1F'},
    0x20: {'plen': 99, 'descr': '子指令数目'},
    0x21: {'plen': 99, 'descr': '检查事件是否触发'},
    0x22: {'plen': 391, 'descr': '部署敌军部队'},
    0x23: {'plen': 0, 'descr': '选择我军出战部队'},
    0x24: {'plen': 3, 'descr': '阵营修改'},
    0x25: {'plen': 2, 'descr': '战场地图名称显示'},
    0x26: {'plen': 3, 'descr': '改变战场地形'},
    0x27: {'plen': 3, 'descr': '战场放火/放水'},
    0x28: {'plen': 3, 'descr': '阵营改变'},
    0x29: {'plen': 0, 'descr': '游戏失败'},
    0x2A: {'plen': 1, 'descr': '显示游戏结局'},
    0x2B: {'plen': 3, 'descr': '给予黄金/残存部队获得经验'},
    0x2C: {'plen': 0, 'descr': '未知指令2C'},
    0x2D: {'plen': 2, 'descr': '兵力士气减半'},
    0x2E: {'plen': 5, 'descr': '切换所在城市'},
    0x2F: {'plen': 3, 'descr': '修改人物未知属性'},
    0x30: {'plen': 2, 'descr': '显示目标（剧情目标或战斗目标）'},
    0x31: {'plen': 0, 'descr': '废弃指令31'},
    0x32: {'plen': 1, 'descr': '废弃指令32'},
    0x33: {'plen': 0, 'descr': '关闭单挑动画'},
    0x34: {'plen': 0, 'descr': '开启单挑动画'},
    0x35: {'plen': 3, 'descr': '单挑动画设定'},
    0x36: {'plen': 0, 'descr': '切换到战斗模式'},
    0x37: {'plen': 3, 'descr': '未知指令37'},
    0x38: {'plen': 1, 'descr': '播放游戏音乐'},
    0x39: {'plen': 3, 'descr': '人物等级上升'},
    0x3A: {'plen': 3, 'descr': '改变人物兵种'},
    0x3B: {'plen': 2, 'descr': '重新定位场景位置'},
    0x3C: {'plen': 2, 'descr': '定位军团'},
    0x3D: {'plen': 1, 'descr': '一般存盘/战场存盘'},
    0xFF: {'plen': 0, 'descr': '本段指令结束'},
}


def get_avatar_name(aid: int) -> str:
    if aid == 0xFFFF:
        return "(未部署/空)"
    if 0 <= aid < len(AVATAR_NAMES):
        return AVATAR_NAMES[aid]
    return f"0x{aid:04X}"


@dataclass
class FriendUnit:
    avatar_id: int = 0xFFFF
    x: int = 0
    y: int = 0
    fixed_01: int = 1
    appear: int = 0      # 0 直接出场, 1 事件出场
    event: int = 0       # 0~255
    direction: int = 0   # 0下, 1左, 2上, 3右
    fubing: int = 0      # 0否, 1是


@dataclass
class FriendDeployment:
    not_retreat: int = 0     # 0 可撤退, 1 不可撤退
    round_cnt: int = 30      # 战斗回合数
    round_inherit: int = 0   # 继承回合数 0 否, 1 是
    opp_main: int = 0xFFFF   # 敌方主将
    my_main: int = 0x0000    # 我方主将
    reserved1: bytes = b"\x00\x01"
    reserved2: bytes = b"\x00\x01"
    units: List[FriendUnit] = field(default_factory=list)


def parse_friend_deployment(buf: bytes) -> FriendDeployment:
    """解析 0x03 我军部队部署指令 (282 字节)"""
    if len(buf) < 282:
        # 如果长度不足，按默认填充
        buf = buf.ljust(282, b"\x00")
    
    not_ret = buf[1]
    round_cnt = buf[2]
    round_inherit = buf[3]
    res1 = bytes(buf[4:6])
    opp_main = struct.unpack('<H', buf[6:8])[0]
    res2 = bytes(buf[8:10])
    my_main = struct.unpack('<H', buf[10:12])[0]
    
    units = []
    for i in range(30):
        st = 12 + i * 9
        aid = struct.unpack('<H', buf[st:st+2])[0]
        x = buf[st+2]
        y = buf[st+3]
        f_01 = buf[st+4]
        appear = buf[st+5]
        ev = buf[st+6]
        d = buf[st+7]
        fu = buf[st+8]
        units.append(FriendUnit(
            avatar_id=aid, x=x, y=y, fixed_01=f_01,
            appear=appear, event=ev, direction=d, fubing=fu
        ))
    
    return FriendDeployment(
        not_retreat=not_ret,
        round_cnt=round_cnt,
        round_inherit=round_inherit,
        opp_main=opp_main,
        my_main=my_main,
        reserved1=res1,
        reserved2=res2,
        units=units
    )


def serialize_friend_deployment(deploy: FriendDeployment, orig_bytes: Optional[bytes] = None) -> bytes:
    """序列化 0x03 我军部队部署指令 (282 字节)"""
    out = bytearray(282)
    out[0] = 0x03
    out[1] = deploy.not_retreat & 0xFF
    out[2] = deploy.round_cnt & 0xFF
    out[3] = deploy.round_inherit & 0xFF
    res1 = deploy.reserved1 if len(deploy.reserved1) == 2 else b"\x00\x01"
    out[4:6] = res1
    struct.pack_into('<H', out, 6, deploy.opp_main & 0xFFFF)
    res2 = deploy.reserved2 if len(deploy.reserved2) == 2 else b"\x00\x01"
    out[8:10] = res2
    struct.pack_into('<H', out, 10, deploy.my_main & 0xFFFF)
    
    for i in range(30):
        st = 12 + i * 9
        if i < len(deploy.units):
            u = deploy.units[i]
            struct.pack_into('<H', out, st, u.avatar_id & 0xFFFF)
            out[st+2] = u.x & 0xFF
            out[st+3] = u.y & 0xFF
            out[st+4] = u.fixed_01 & 0xFF
            out[st+5] = u.appear & 0xFF
            out[st+6] = u.event & 0xFF
            out[st+7] = u.direction & 0xFF
            out[st+8] = u.fubing & 0xFF
        else:
            struct.pack_into('<H', out, st, 0xFFFF)
            out[st+4] = 0x01
    
    return bytes(out)


@dataclass
class EnemyUnit:
    avatar_id: int = 0xFFFF
    x: int = 0
    y: int = 0
    appear: int = 0      # 0 直接出场, 1 事件出场
    event: int = 0       # 0~255
    direction: int = 0   # 0下, 1左, 2上, 3右
    fubing: int = 0      # 0否, 1是
    ai_type: int = 0     # 0~7
    ai_param1: int = 0   # 目标X 或 仇人 low byte
    ai_param2: int = 0   # 目标Y 或 仇人 high byte
    bingzhong: int = 0   # 0~18 (短兵, 长兵...)
    level: int = 1       # 1~99


@dataclass
class EnemyDeployment:
    units: List[EnemyUnit] = field(default_factory=list)


def parse_enemy_deployment(buf: bytes) -> EnemyDeployment:
    """解析 0x22 敌军部队部署指令 (392 字节)"""
    if len(buf) < 392:
        buf = buf.ljust(392, b"\x00")
    
    units = []
    for i in range(30):
        st = 2 + i * 13
        aid = struct.unpack('<H', buf[st:st+2])[0]
        x = buf[st+2]
        y = buf[st+3]
        appear = buf[st+4]
        ev = buf[st+5]
        d = buf[st+6]
        fu = buf[st+7]
        ai = buf[st+8]
        p1 = buf[st+9]
        p2 = buf[st+10]
        bz = buf[st+11]
        lv = buf[st+12]
        units.append(EnemyUnit(
            avatar_id=aid, x=x, y=y,
            appear=appear, event=ev, direction=d, fubing=fu,
            ai_type=ai, ai_param1=p1, ai_param2=p2,
            bingzhong=bz, level=lv
        ))
    return EnemyDeployment(units=units)


def serialize_enemy_deployment(deploy: EnemyDeployment) -> bytes:
    """序列化 0x22 敌军部队部署指令 (392 字节)"""
    out = bytearray(392)
    out[0] = 0x22
    out[1] = 0x00
    for i in range(30):
        st = 2 + i * 13
        if i < len(deploy.units):
            u = deploy.units[i]
            struct.pack_into('<H', out, st, u.avatar_id & 0xFFFF)
            out[st+2] = u.x & 0xFF
            out[st+3] = u.y & 0xFF
            out[st+4] = u.appear & 0xFF
            out[st+5] = u.event & 0xFF
            out[st+6] = u.direction & 0xFF
            out[st+7] = u.fubing & 0xFF
            out[st+8] = u.ai_type & 0xFF
            out[st+9] = u.ai_param1 & 0xFF
            out[st+10] = u.ai_param2 & 0xFF
            out[st+11] = u.bingzhong & 0xFF
            out[st+12] = u.level & 0xFF
        else:
            struct.pack_into('<H', out, st, 0xFFFF)
            out[st+12] = 0x01
    return bytes(out)


class ScriptInstruction:
    """单条战斗/剧情指令"""

    def __init__(self, raw_bytes: bytes):
        self.raw_bytes = bytearray(raw_bytes)
        self.opcode = raw_bytes[0] if raw_bytes else 0

    @property
    def hex_code(self) -> str:
        return ' '.join(f'{b:02x}' for b in self.raw_bytes)

    @property
    def opcode_name(self) -> str:
        step_info = CODE_STEPS.get(self.opcode)
        return step_info['descr'] if step_info else f"未知指令 (0x{self.opcode:02X})"

    @property
    def detail(self) -> str:
        """解析指令的可读中文参数释义"""
        buf = self.raw_bytes
        c = self.opcode
        length = len(buf)

        if c == 0x10 and length >= 5:  # 单挑
            a1 = struct.unpack('<H', buf[1:3])[0]
            a2 = struct.unpack('<H', buf[3:5])[0]
            return f"武将单挑: [{get_avatar_name(a1)}] VS [{get_avatar_name(a2)}]"

        elif c == 0x1C and length >= 4:  # 改变 AI
            aid = struct.unpack('<H', buf[1:3])[0]
            ai_type = buf[3]
            ai_str = AI_TYPES.get(ai_type, f"AI模式{ai_type}")
            return f"改变 [{get_avatar_name(aid)}] AI -> {ai_str}"

        elif c == 0x14 and length >= 3:  # 事件开关
            ev_id = buf[1]
            status = buf[2]
            return f"设置事件开关: 标志0x{ev_id:02X} = {status}"

        elif c == 0x21 and length >= 4:  # 条件触发检查
            ign_cnt = buf[1]
            tg1_cnt = buf[2]
            return f"检查条件: 未满足跳过{ign_cnt}条指令 (已触发条件数={tg1_cnt})"

        elif c in (0x01, 0x0A) and length >= 6:  # 部署非战斗人物/移动
            aid = struct.unpack('<H', buf[1:3])[0]
            x, y, direct = buf[3], buf[4], buf[5]
            dir_str = DIRECTIONS.get(direct, f"朝向{direct}")
            return f"部署人物: [{get_avatar_name(aid)}] 坐标({x},{y}) {dir_str}"

        elif c == 0x1B and length >= 2:  # 获得道具
            it_id = buf[1]
            it_name = DAOJU_LIST[it_id] if it_id < len(DAOJU_LIST) else f"道具0x{it_id:02X}"
            return f"获得道具: [{it_name}] (ID=0x{it_id:02X})"

        elif c == 0x17 and length >= 2:  # 剧情模式
            st = "开启" if buf[1] == 1 else "关闭"
            return f"剧情模式开关: {st}"

        elif c in (0x24, 0x28) and length >= 4:  # 修改阵营
            aid = struct.unpack('<H', buf[1:3])[0]
            target_f = buf[3] + 0x80
            f_name = JUNTUAN_MAP.get(target_f, f"阵营0x{target_f:02X}")
            return f"改变 [{get_avatar_name(aid)}] 阵营 -> {f_name}"

        elif c == 0x27 and length >= 4:  # 放火放水
            x, y, what = buf[1], buf[2], buf[3]
            what_str = "放火" if what == 0 else ("放水" if what == 1 else "取消")
            return f"战场地图 ({x},{y}) {what_str}"

        elif c == 0x1A and length >= 3:  # 援军出现
            aid = struct.unpack('<H', buf[1:3])[0]
            return f"援军登场: [{get_avatar_name(aid)}]"

        elif c == 0x18 and length >= 3:  # 撤退/消失
            aid = struct.unpack('<H', buf[1:3])[0]
            return f"部队撤退/消失: [{get_avatar_name(aid)}]"

        elif c == 0x23:
            return "战场选择我军出战部队"

        elif c == 0x26:
            return "改变战场地形"

        elif c == 0x29:
            return "判定本场战斗失败！"

        elif c == 0x2B and length >= 4:
            val_type = "金钱" if buf[1] == 0x02 else "经验"
            amount = struct.unpack('<H', buf[2:4])[0]
            return f"获得奖励: {val_type} +{amount}"

        elif c == 0x39 and length >= 4:
            aid = struct.unpack('<H', buf[1:3])[0]
            up_lv = buf[3]
            return f"[{get_avatar_name(aid)}] 升级 +{up_lv}级"

        elif c == 0x2E and length >= 3:
            city_id = struct.unpack('<H', buf[1:3])[0]
            return f"切换所在城市 ID={city_id}"

        elif c == 0x03 and length >= 12:
            not_ret = buf[1]
            rounds = buf[2]
            opp = struct.unpack('<H', buf[6:8])[0]
            my = struct.unpack('<H', buf[10:12])[0]
            cnt = 0
            for i in range(30):
                st = 12 + i * 9
                if st + 2 <= length:
                    aid = struct.unpack('<H', buf[st:st+2])[0]
                    if aid != 0xFFFF:
                        cnt += 1
            opp_str = get_avatar_name(opp) if opp != 0xFFFF else '无'
            my_str = get_avatar_name(my)
            ret_str = '不可撤退' if not_ret else '可撤退'
            return f"部署我军: 我将[{my_str}] 敌将[{opp_str}] {rounds}回合({ret_str}) 已部署{cnt}/30人"

        elif c == 0x22 and length >= 2:
            cnt = 0
            first_name = ""
            for i in range(30):
                st = 2 + i * 13
                if st + 2 <= length:
                    aid = struct.unpack('<H', buf[st:st+2])[0]
                    if aid != 0xFFFF:
                        cnt += 1
                        if not first_name:
                            first_name = get_avatar_name(aid)
            lead_str = f"领将[{first_name}]等 " if first_name else ""
            return f"部署敌军: {lead_str}已配置{cnt}/30支敌方部队阵容"

        return ""


class SnrdSection:
    """一个事件节（包含触发器条件和指令序列）"""

    def __init__(self, header_bytes: bytes, script_bytes: bytes):
        self.header_bytes = bytearray(header_bytes)  # 10 字节表头
        self.trigger_id = self.header_bytes[0] if self.header_bytes else 0
        self.instructions: List[ScriptInstruction] = []
        self._parse_script(script_bytes)

    @property
    def trigger_name(self) -> str:
        return TRIGGER_DESCR.get(self.trigger_id, f"触发条件(0x{self.trigger_id:02X})")

    def _parse_script(self, script_bytes: bytes):
        self.instructions = []
        i = 0
        n = len(script_bytes)
        while i < n:
            b = script_bytes[i]
            if b == 0x20 or b == 0x32:
                step = script_bytes[i + 1] + 1 if i + 1 < n else 0
                if step > 0x80:
                    step -= 0x80
            elif b == 0x21:
                # 变长检查指令
                ign_cnt = script_bytes[i + 1] if i + 1 < n else 0
                tg1_cnt = script_bytes[i + 2] if i + 2 < n else 0
                idx_tg0 = i + 3 + tg1_cnt
                tg0_cnt = script_bytes[idx_tg0] if idx_tg0 < n else 0
                step = 3 + tg1_cnt + tg0_cnt
            else:
                step_info = CODE_STEPS.get(b)
                step = step_info['plen'] if step_info else 0

            end = min(n, i + step + 1)
            chunk = script_bytes[i:end]
            self.instructions.append(ScriptInstruction(chunk))
            i = end


class SnrdParagraph:
    """一个段落（包含若干 Section）"""

    def __init__(self):
        self.sections: List[SnrdSection] = []


class SnrdPage:
    """一个 Page（大战场/大场景）"""

    def __init__(self, page_index: int):
        self.page_index = page_index
        self.paragraphs: List[SnrdParagraph] = []


class SnrdChapter:
    """单章节剧本指令文件对象 (SnrXd.r3)"""

    def __init__(self, chapter_num: int, file_path: str):
        self.chapter_num = chapter_num
        self.file_path = os.path.abspath(file_path)
        self.filename = os.path.basename(file_path)
        self.ls11_header = b""
        self.pages: List[SnrdPage] = []
        self._load()

    @property
    def backup_path(self) -> str:
        return f"{self.file_path}.bak"

    @property
    def has_backup(self) -> bool:
        return os.path.isfile(self.backup_path)

    def _load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"未找到剧本指令文件: {self.file_path}")

        with open(self.file_path, "rb") as fp:
            self.ls11_header = fp.read(0x110)
            self.pages = []

            # 1. 读取 Page 索引 (大端序: >III)
            page_meta = []
            while True:
                buf = fp.read(12)
                if len(buf) < 12:
                    break
                sz_comp, sz_orig, offset = struct.unpack('>III', buf)
                if sz_comp == 0:
                    break
                page_meta.append((sz_comp, sz_orig, offset))

            # 2. 读取每个 Page
            for p_idx, (sz_comp, sz_orig, p_offset) in enumerate(page_meta):
                page_obj = SnrdPage(p_idx)
                fp.seek(p_offset)

                # 读取 Paragraph 偏移表 (以 0xFFFF 结尾)
                p_offsets = []
                while True:
                    b_off = fp.read(2)
                    if len(b_off) < 2:
                        break
                    val = struct.unpack('<H', b_off)[0]
                    if val == 0xFFFF:
                        break
                    p_offsets.append(val)

                # 读取每个 Paragraph
                for pg_idx, pg_rel_off in enumerate(p_offsets):
                    pg_obj = SnrdParagraph()
                    pg_abs_off = p_offset + pg_rel_off
                    fp.seek(pg_abs_off)

                    # 读取 Section 列表 (10 字节表头以 0xFF 0xFF 结尾)
                    sec_headers = []
                    while True:
                        hdr = fp.read(10)
                        if len(hdr) < 10:
                            break
                        if hdr[0] == 0xFF and hdr[1] == 0xFF:
                            break
                        sec_headers.append(hdr)

                    # 读取每个 Section 对应的 Script 指令流
                    for s_idx, hdr in enumerate(sec_headers):
                        rel_script_off = struct.unpack('<H', hdr[8:10])[0]
                        script_abs_off = pg_abs_off + rel_script_off
                        # 判断脚本长度
                        if s_idx < len(sec_headers) - 1:
                            next_rel = struct.unpack('<H', sec_headers[s_idx + 1][8:10])[0]
                            script_len = next_rel - rel_script_off
                        else:
                            # 最后一项，到下一个段落或下一个Page
                            if pg_idx < len(p_offsets) - 1:
                                next_pg_abs = p_offset + p_offsets[pg_idx + 1]
                                script_len = max(0, next_pg_abs - script_abs_off)
                            elif p_idx < len(page_meta) - 1:
                                next_p_abs = page_meta[p_idx + 1][2]
                                script_len = max(0, next_p_abs - script_abs_off)
                            else:
                                cur_pos = fp.tell()
                                fp.seek(0, 2)
                                script_len = max(0, fp.tell() - script_abs_off)
                                fp.seek(cur_pos)

                        fp.seek(script_abs_off)
                        raw_script = fp.read(script_len)
                        sec_obj = SnrdSection(hdr, raw_script)
                        pg_obj.sections.append(sec_obj)

                    page_obj.paragraphs.append(pg_obj)

                self.pages.append(page_obj)

    def save(self, target_path: Optional[str] = None):
        """将修改后的指令回写并重构偏移结构"""
        dst = target_path if target_path else self.file_path

        if not self.has_backup:
            shutil.copyfile(self.file_path, self.backup_path)

        with open(dst, "wb") as fp:
            fp.write(self.ls11_header)

            page_index_offset = fp.tell()
            for _ in range(len(self.pages)):
                fp.write(b"\x00" * 12)
            fp.write(b"\x00" * 4)

            page_offset_list = []

            for p_idx, page in enumerate(self.pages):
                page_offset_list.append(fp.tell())
                paragraph_index_offset = fp.tell()

                for _ in range(len(page.paragraphs)):
                    fp.write(b"\x00\x00")
                fp.write(b"\xff\xff")

                paragraph_offset_list = []
                for pg_idx, paragraph in enumerate(page.paragraphs):
                    paragraph_offset_list.append(fp.tell() - paragraph_index_offset)
                    section_index_offset = fp.tell()

                    # 写入 Section 10 字节表头
                    for sec in paragraph.sections:
                        fp.write(sec.header_bytes)
                    fp.write(b"\xff" * 10)

                    section_offset_list = []
                    for sec in paragraph.sections:
                        section_offset_list.append(fp.tell() - section_index_offset)
                        for ins in sec.instructions:
                            fp.write(ins.raw_bytes)

                    end_offset = fp.tell()

                    # 回填 Section 偏移
                    saved = fp.tell()
                    fp.seek(section_index_offset)
                    for s_idx in range(len(paragraph.sections)):
                        fp.seek(8, 1)
                        off = section_offset_list[s_idx]
                        fp.write(struct.pack("<H", off))
                        paragraph.sections[s_idx].header_bytes[8:10] = struct.pack("<H", off)
                    fp.seek(saved)

                # 回填 Paragraph 偏移
                saved = fp.tell()
                fp.seek(paragraph_index_offset)
                for pg_idx in range(len(page.paragraphs)):
                    off = paragraph_offset_list[pg_idx]
                    fp.write(struct.pack("<H", off))
                fp.seek(saved)

            # 回填 Page 偏移 (大端序)
            saved = fp.tell()
            fp.seek(page_index_offset)
            for p_idx in range(len(self.pages)):
                if p_idx < len(self.pages) - 1:
                    length = page_offset_list[p_idx + 1] - page_offset_list[p_idx]
                else:
                    length = end_offset - page_offset_list[p_idx]

                fp.write(struct.pack(">III", length, length, page_offset_list[p_idx]))
            fp.seek(saved)

    def restore_from_backup(self):
        if not self.has_backup:
            raise FileNotFoundError(f"未找到可还原的备份文件 ({self.filename}.bak)！")
        shutil.copyfile(self.backup_path, self.file_path)
        self._load()


class SnrdManager:
    """管理游戏目录下的 Snr0d.r3 ~ Snr4d.r3"""

    def __init__(self, game_dir: str):
        self.game_dir = os.path.abspath(game_dir)
        self.chapters: Dict[int, SnrdChapter] = {}
        self._detect_chapters()

    def _detect_chapters(self):
        for ch in range(5):
            fname = f"Snr{ch}d.r3"
            target_path = None
            for f in os.listdir(self.game_dir):
                if f.lower() == fname.lower():
                    target_path = os.path.join(self.game_dir, f)
                    break
            if target_path and os.path.isfile(target_path):
                try:
                    self.chapters[ch] = SnrdChapter(ch, target_path)
                except Exception as e:
                    print(f"载入剧本指令章节 {ch} 失败: {e}")

    @property
    def available_chapters(self) -> List[int]:
        return sorted(list(self.chapters.keys()))

    def get_chapter(self, ch_num: int) -> Optional[SnrdChapter]:
        return self.chapters.get(ch_num)

    def save_all_chapters(self):
        for ch in self.chapters.values():
            ch.save()

    def restore_all_backups(self) -> List[str]:
        restored = []
        for ch in self.chapters.values():
            if ch.has_backup:
                ch.restore_from_backup()
                restored.append(ch.filename)
        return restored
