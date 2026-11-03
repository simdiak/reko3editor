"""
《三国志英杰传》武将三项能力 (Bakdata.r3) 管理模块
负责解析与修改 384 位武将的武力、智力、统御三维基础能力
"""

import os
import shutil
from typing import List, Optional

# 兜底武将名列表（前 255 位等知名武将）
FALLBACK_AVATAR_NAMES = [
    '劉備', '關羽', '張飛', '董卓', '呂布', '華雄', '李儒', '孔融', '曹操', '袁紹',
    '孫堅', '袁術', '公孫瓚', '程普', '黃蓋', '陶謙', '夏侯惇', '夏侯淵', '曹仁', '曹洪',
    '李肅', '胡軫', '楊昂', '黃權', '閻圃', '公孫越', '曹豹', '趙岑', '呂建', '關興',
    '馬謖', '李豐', '徐商', '廖化', '沙摩可', '荀爽', '杜襲', '王甫', '趙累', '劉岱',
    '張邈', '孫桓', '袁胤', '張苞', '韓當', '朱然', '李傕', '郭汜', '徐榮', '田豐',
    '沮授', '顏良', '文醜', '趙雲', '逢紀', '許攸', '陳震', '耿武', '關純', '嚴綱',
    '麴義', '郭嘉', '于禁', '孫乾', '糜竺', '陳登', '樂就', '許褚', '荀彧', '紀靈',
    '董昭', '陳紀', '高順', '魏續', '宋憲', '陳宮', '荀攸', '程昱', '徐晃', '張遼',
    '侯成', '糜芳', '簡雍', '滿寵', '許汜', '王楷', '郝萌', '曹性', '孫觀', '車冑',
    '吳班', '審配', '郭圖', '賈詡', '劉表', '朱靈', '路昭', '馬騰', '陳琳', '王忠',
    '劉瞱', '張繡', '張郃', '高覽', '韓猛', '淳于瓊', '蔣奇', '馬忠', '李異', '謝旌',
    '辛明', '徐庶', '蔡瑁', '伊籍', '劉琦', '李典', '劉封', '張武', '陳孫', '蒯越',
    '劉琮', '文聘', '王威', '呂曠', '呂翔', '諸葛亮', '魏延', '關平', '夏侯蘭', '韓浩',
    '張允', '李珪', '龐統', '王粲', '宋忠', '夏侯恩', '晏明', '馬延', '焦觸', '張南',
    '夏侯傑', '孫權', '周瑜', '魯肅', '張昭', '諸葛瑾', '闞澤', '甘寧', '呂蒙', '太史慈',
    '陸遜', '鮑龍', '蔡陽', '蔡中', '周倉', '顧雍', '虞翻', '步騭', '薛綜', '陸績',
    '嚴畯', '蔣欽', '周泰', '蔡勳', '丁奉', '徐盛', '凌統', '陳武', '毛玠', '黃忠',
    '牛金', '陳矯', '曹純', '潘璋', '馬良', '劉度', '劉賢', '邢道榮', '趙範', '陳應',
    '金旋', '鞏志', '韓玄', '楊齡', '孫瑜', '呂範', '張松', '法正', '劉璋', '馬超',
    '孟達', '王累', '李恢', '劉貴', '冷苞', '張任', '鄧賢', '楊懷', '高沛', '吳懿',
    '吳蘭', '雷銅', '嚴顏', '馬岱', '張魯', '張衛', '楊任', '霍峻', '陳式', '夏侯尚',
    '夏侯德', '曹彰', '曹丕', '司馬懿', '曹休', '龐德', '管亥', '樂進', '王鐵', '蔣然',
    '藩宮', '羽則', '周比', '趙何', '楊彥', '楊綱', '侯累', '陳蔣', '董梁', '李雄',
    '嚴雙', '朱康', '吳祖', '孟肅', '程德', '張獲', '高蒼', '宋費', '曹植', '司馬師',
    '司馬昭', '曹真', '郝昭', '姜維', '韓英', '郭適', '杨玄', '劉辟', '劉循', '楊松',
    '楊修', '王平', '劉禪', '李嚴', '費觀', '韓暹'
]


class AvatarStats:
    """单个武将的三维能力模型"""

    def __init__(self, index: int, name: str, tongyu: int, wuli: int, zhili: int):
        self.index = index
        self.name = name
        self.tongyu = max(0, min(100, int(tongyu)))  # 统御 0~100
        self.wuli = max(0, min(100, int(wuli)))      # 武力 0~100
        self.zhili = max(0, min(100, int(zhili)))    # 智力 0~100

    @property
    def total(self) -> int:
        """三维总和"""
        return self.tongyu + self.wuli + self.zhili


class BakdataManager:
    """Bakdata.r3 档案解析与回写管理器"""

    EXPECTED_SIZE = 19328  # 官方 Bakdata.r3 文件大小
    DATA_START_OFFSET = 0x1100  # 武将数据起始偏移
    RECORD_SIZE = 21  # 每人 21 字节 (0x15)
    TOTAL_AVATARS = 384  # 总共 384 名武将

    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self.filename = os.path.basename(file_path)
        self.raw_data: bytearray = bytearray()
        self.avatars: List[AvatarStats] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"未找到基础数据文件:\n{self.file_path}")

        with open(self.file_path, 'rb') as f:
            data = f.read()

        if len(data) != self.EXPECTED_SIZE:
            raise ValueError(
                f"Bakdata.r3 文件大小不符合规范: 预期 {self.EXPECTED_SIZE} 字节，实际 {len(data)} 字节"
            )

        self.raw_data = bytearray(data)
        self.avatars = []

        for i in range(self.TOTAL_AVATARS):
            offset = self.DATA_START_OFFSET + i * self.RECORD_SIZE
            chunk = self.raw_data[offset : offset + self.RECORD_SIZE]

            # 读取武将名
            raw_name = bytes(chunk[:6]).split(b'\x00')[0]
            try:
                name = raw_name.decode('big5').strip()
            except Exception:
                name = ""

            if not name:
                name = (
                    FALLBACK_AVATAR_NAMES[i]
                    if i < len(FALLBACK_AVATAR_NAMES)
                    else f"武将_{i}"
                )

            tongyu = chunk[17]
            wuli = chunk[18]
            zhili = chunk[19]

            self.avatars.append(AvatarStats(i, name, tongyu, wuli, zhili))

    @property
    def backup_path(self) -> str:
        return f"{self.file_path}.bak"

    @property
    def has_backup(self) -> bool:
        return os.path.isfile(self.backup_path)

    def save(self, target_path: Optional[str] = None):
        """将武将三项能力写回二进制并保存"""
        dst = target_path if target_path else self.file_path

        # 首次保存前自动备份
        if not self.has_backup:
            shutil.copyfile(self.file_path, self.backup_path)

        # 写入 384 位武将的统御、武力、智力
        for i, a in enumerate(self.avatars):
            offset = self.DATA_START_OFFSET + i * self.RECORD_SIZE
            self.raw_data[offset + 17] = a.tongyu & 0xFF
            self.raw_data[offset + 18] = a.wuli & 0xFF
            self.raw_data[offset + 19] = a.zhili & 0xFF

        if len(self.raw_data) != self.EXPECTED_SIZE:
            raise ValueError("写入数据长度异常，保存中止！")

        with open(dst, 'wb') as f:
            f.write(self.raw_data)

    def restore_from_backup(self):
        """从 .bak 备份文件还原"""
        if not self.has_backup:
            raise FileNotFoundError("未找到可供还原的备份文件 (Bakdata.r3.bak)！")

        shutil.copyfile(self.backup_path, self.file_path)
        self._load()

