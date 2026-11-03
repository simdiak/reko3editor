"""
《三国志英杰传》存档解析与回写核心模块
负责解析与保存 MSAVE*.R3S 存档文件结构
"""

import os
import struct
from typing import List, Optional
from msave_editor.constants import (
    JUNTUAN_MAP,
    JUNTUAN_NAME_TO_ID,
    BINGZHONG_LIST,
    BINGZHONG_NAME_TO_ID,
    DAOJU_LIST,
    DAOJU_NAME_TO_ID,
    AVATAR_NAMES
)


class Avatar:
    """单个武将的数据对象（对应存档中 18 字节记录）"""

    def __init__(self, index: int, raw_bytes: bytes):
        self.index = index
        self.raw_bytes = bytearray(raw_bytes)
        self.hex_id = f"0x{index:03X}"
        self.name = AVATAR_NAMES[index] if index < len(AVATAR_NAMES) else f"武将_{index}"

        # 字节 0: 军团 ID
        self.juntuan_id = self.raw_bytes[0]
        self.juntuan_name = JUNTUAN_MAP.get(self.juntuan_id, f"未知(0x{self.juntuan_id:02X})")

        # 字节 1: 登场/状态标记
        self.status = self.raw_bytes[1]

        # 字节 4: 士气 / 忠诚度
        self.morale = self.raw_bytes[4]

        # 字节 5~6: 兵力 (小端 16位整数)
        self.troop = struct.unpack('<H', self.raw_bytes[5:7])[0]

        # 字节 7: 兵种 ID
        self.bingzhong_id = self.raw_bytes[7]
        self.bingzhong_name = (
            BINGZHONG_LIST[self.bingzhong_id]
            if self.bingzhong_id < len(BINGZHONG_LIST)
            else f"未知({self.bingzhong_id})"
        )

        # 字节 8: 等级
        self.level = self.raw_bytes[8]

        # 字节 9: 经验
        self.exp = self.raw_bytes[9]

        # 字节 10~17: 8 个道具槽
        self.item_ids = list(self.raw_bytes[10:18])
        self._refresh_item_names()

    def _refresh_item_names(self):
        """刷新道具名称列表"""
        self.item_names = [
            DAOJU_LIST[it] if it < len(DAOJU_LIST) else f"0x{it:02X}"
            for it in self.item_ids
            if it != 0xFF
        ]

    @property
    def is_liubei_army(self) -> bool:
        """是否属于刘备军"""
        return self.juntuan_id == 0x80

    @property
    def items_summary(self) -> str:
        """道具摘要字符串"""
        return "、".join(self.item_names) if self.item_names else "-"

    def set_juntuan(self, name_or_id):
        """设置所属军团"""
        if isinstance(name_or_id, int):
            self.juntuan_id = name_or_id
            self.juntuan_name = JUNTUAN_MAP.get(name_or_id, f"0x{name_or_id:02X}")
        else:
            if name_or_id in JUNTUAN_NAME_TO_ID:
                self.juntuan_id = JUNTUAN_NAME_TO_ID[name_or_id]
                self.juntuan_name = name_or_id

    def set_bingzhong(self, name_or_id):
        """设置兵种"""
        if isinstance(name_or_id, int):
            self.bingzhong_id = name_or_id
            self.bingzhong_name = (
                BINGZHONG_LIST[name_or_id]
                if name_or_id < len(BINGZHONG_LIST)
                else f"未知({name_or_id})"
            )
        else:
            if name_or_id in BINGZHONG_NAME_TO_ID:
                self.bingzhong_id = BINGZHONG_NAME_TO_ID[name_or_id]
                self.bingzhong_name = name_or_id

    def set_level(self, val: int):
        self.level = max(1, min(99, int(val)))

    def set_exp(self, val: int):
        self.exp = max(0, min(99, int(val)))

    def set_troop(self, val: int):
        self.troop = max(0, min(65535, int(val)))

    def set_morale(self, val: int):
        self.morale = max(0, min(100, int(val)))

    def set_item_slot(self, slot_idx: int, item_name_or_id):
        """设置指定格子(0~7)的道具，None/0xFF/'(空)'表示清空"""
        if slot_idx < 0 or slot_idx >= 8:
            return

        if item_name_or_id in (None, 0xFF, '', '(空)', '-'):
            self.item_ids[slot_idx] = 0xFF
        elif isinstance(item_name_or_id, int):
            self.item_ids[slot_idx] = item_name_or_id & 0xFF
        elif item_name_or_id in DAOJU_NAME_TO_ID:
            self.item_ids[slot_idx] = DAOJU_NAME_TO_ID[item_name_or_id]
        self._refresh_item_names()

    def serialize(self) -> bytes:
        """将当前武将属性序列化回 18 字节二进制"""
        buf = bytearray(self.raw_bytes)
        buf[0] = self.juntuan_id & 0xFF
        buf[1] = self.status & 0xFF
        # 字节 2~3 保持不变
        buf[4] = self.morale & 0xFF
        struct.pack_into('<H', buf, 5, self.troop & 0xFFFF)
        buf[7] = self.bingzhong_id & 0xFF
        buf[8] = self.level & 0xFF
        buf[9] = self.exp & 0xFF
        for i in range(8):
            buf[10 + i] = self.item_ids[i] & 0xFF
        self.raw_bytes = buf
        return bytes(buf)


class SaveFile:
    """存档文件对象"""
    EXPECTED_SIZE = 8789  # 0x2255 字节

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.raw_data = bytearray()
        self.title = ""
        self.money = 0
        self.avatars: List[Avatar] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"存档文件不存在: {self.filepath}")

        with open(self.filepath, 'rb') as f:
            data = f.read()

        if len(data) != self.EXPECTED_SIZE:
            raise ValueError(
                f"存档文件大小不符合规范: 预期 {self.EXPECTED_SIZE} 字节，实际 {len(data)} 字节"
            )

        self.raw_data = bytearray(data)

        # 1. 解析章节标题（偏移 0x05 开始，Big5 解码，遇 \x00 截断）
        title_raw = bytes(self.raw_data[5:0x20]).split(b'\x00')[0]
        try:
            self.title = title_raw.decode('big5').strip()
        except Exception:
            self.title = title_raw.decode('big5', errors='replace').strip()

        # 2. 解析金钱（偏移 0x23, 2字节小端 uint16）
        self.money = struct.unpack('<H', self.raw_data[0x23:0x25])[0]

        # 3. 解析 384 名武将数据（偏移 0x695 开始，每人 18 字节）
        self.avatars = []
        start_offset = 0x695
        for i in range(384):
            offset = start_offset + i * 18
            chunk = bytes(self.raw_data[offset : offset + 18])
            self.avatars.append(Avatar(i, chunk))

    def set_money(self, val: int):
        """设置军团金钱（最高 10000）"""
        self.money = max(0, min(10000, int(val)))

    def save(self, filepath: Optional[str] = None):
        """将当前内存数据写回文件"""
        target_path = filepath if filepath else self.filepath

        # 1. 写回金钱到偏移 0x23:0x25
        struct.pack_into('<H', self.raw_data, 0x23, self.money & 0xFFFF)

        # 2. 写回 384 位武将数据到 0x695
        start_offset = 0x695
        for i, avatar in enumerate(self.avatars):
            offset = start_offset + i * 18
            avatar_bytes = avatar.serialize()
            self.raw_data[offset : offset + 18] = avatar_bytes

        if len(self.raw_data) != self.EXPECTED_SIZE:
            raise ValueError("写入数据长度异常，保存中止！")

        # 3. 写入文件
        with open(target_path, 'wb') as f:
            f.write(self.raw_data)

        self.filepath = target_path
        self.filename = os.path.basename(target_path)

    def filter_avatars(
        self,
        juntuan_filter: Optional[str] = None,
        search_keyword: Optional[str] = None,
        has_items_only: bool = False
    ) -> List[Avatar]:
        """按军团、关键字、道具条件筛选武将"""
        results = self.avatars

        if juntuan_filter and juntuan_filter != "全部军团":
            results = [a for a in results if a.juntuan_name == juntuan_filter]

        if has_items_only:
            results = [a for a in results if len(a.item_names) > 0]

        if search_keyword:
            kw = search_keyword.strip().lower()
            results = [
                a for a in results
                if kw in a.name.lower()
                or kw in str(a.index)
                or kw in a.hex_id.lower()
                or kw in a.bingzhong_name.lower()
                or any(kw in it.lower() for it in a.item_names)
            ]

        return results
