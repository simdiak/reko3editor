"""
《三国志英杰传》剧情文本 (SNRM) 解析与回写管理模块
负责各章节 (Snr0m.r3 ~ Snr4m.r3) 剧情文本与武将对话的提取、编辑与重构
"""

import os
import shutil
import struct
from typing import List, Optional, Tuple, Dict
from prog_editor.bakdata import FALLBACK_AVATAR_NAMES

CHAPTER_TITLES = {
    0: "序章　群雄起兵討伐董卓",
    1: "第一章　界橋之戰",
    2: "第二章　官渡之戰",
    3: "第三章　赤壁之戰 / 蜀漢建國",
    4: "第四章　蜀魏最後決戰",
}


class TextItem:
    """单个剧情对白/旁白文本对象"""

    def __init__(
        self,
        index: int,
        page: int,
        avatar_id: Optional[int],
        text: str,
        is_dialogue: bool,
        raw_tail: bytes = b"\x00"
    ):
        self.index = index
        self.page = page
        self.avatar_id = avatar_id
        self.is_dialogue = is_dialogue
        self.text = text
        self.raw_tail = raw_tail  # 结尾分隔符（通常为 \x00 或 \xff\xff）

    @property
    def speaker_name(self) -> str:
        """说话武将姓名或旁白"""
        if self.is_dialogue and self.avatar_id is not None:
            if self.avatar_id < len(FALLBACK_AVATAR_NAMES):
                return FALLBACK_AVATAR_NAMES[self.avatar_id]
            return f"武将_{self.avatar_id}"
        return "旁白 / 系统"

    @property
    def type_desc(self) -> str:
        return "武将对白" if self.is_dialogue else "旁白/描述"

    @property
    def preview(self) -> str:
        """单行简略摘要"""
        clean = self.text.replace("\r", " ").replace("\n", " ").strip()
        return clean[:50] + ("..." if len(clean) > 50 else "")

    def check_big5_compatible(self) -> Tuple[bool, str]:
        """检查当前文本是否能被 Big5 编码"""
        try:
            self.text.encode("big5")
            return True, ""
        except UnicodeEncodeError as e:
            bad_char = self.text[e.start:e.end]
            return False, f"字符 '{bad_char}' 无法转换为 Big5 繁体编码"

    def serialize(self) -> bytes:
        """序列化为游戏原始字节流"""
        txt_encoded = self.text.encode("big5", errors="replace")
        if self.is_dialogue and self.avatar_id is not None:
            prefix = struct.pack("<H", self.avatar_id & 0xFFFF)
            return prefix + txt_encoded + self.raw_tail
        else:
            return txt_encoded + self.raw_tail


class SnrChapter:
    """单章节剧本剧情对象"""

    def __init__(self, chapter_num: int, file_path: str):
        self.chapter_num = chapter_num
        self.file_path = os.path.abspath(file_path)
        self.filename = os.path.basename(file_path)
        self.title = CHAPTER_TITLES.get(chapter_num, f"第{chapter_num}章")
        self.items: List[TextItem] = []
        self.page_count = 0
        self._load()

    @property
    def backup_path(self) -> str:
        return f"{self.file_path}.bak"

    @property
    def has_backup(self) -> bool:
        return os.path.isfile(self.backup_path)

    def _load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"未找到剧本文件: {self.file_path}")

        with open(self.file_path, "rb") as fp:
            data = fp.read()

        if len(data) < 4:
            raise ValueError(f"剧本文件 {self.filename} 大小过小！")

        data_offset = struct.unpack("<H", data[:2])[0]
        self.page_count = data_offset // 2

        offsets = []
        for i in range(self.page_count):
            offsets.append(struct.unpack("<H", data[i * 2 : i * 2 + 2])[0])
        offsets.append(len(data))

        self.items = []
        global_idx = 0

        for page in range(self.page_count):
            start = offsets[page]
            end = offsets[page + 1]
            pos = start

            while pos < end:
                # 寻找单条记录结束位置
                cur_start = pos
                buf = bytearray()
                last_c = 0
                while pos < end:
                    c = data[pos]
                    pos += 1
                    # 规则1: 长度大于2且遇到 \x00 为正常文本结束
                    if len(buf) > 2 and c == 0:
                        break
                    # 规则2: 遇到连续的 0xFF 0xFF 为特殊结束标记
                    if c == 0xFF and last_c == 0xFF:
                        buf.append(c)
                        break
                    buf.append(c)
                    last_c = c

                tail = b"\x00"
                if len(buf) >= 2 and buf[-2:] == b"\xff\xff":
                    tail = b"\xff\xff"
                    content_bytes = bytes(buf[:-2])
                else:
                    content_bytes = bytes(buf)

                avatar_id = None
                is_dialogue = False
                text = ""

                # 识别是否为带头像对话
                if len(content_bytes) >= 2 and content_bytes[0] != 0xFF:
                    aid = struct.unpack("<H", content_bytes[:2])[0]
                    if aid < 0x180:  # 384 以内为武将 ID
                        avatar_id = aid
                        is_dialogue = True
                        try:
                            text = content_bytes[2:].decode("big5")
                        except Exception:
                            text = content_bytes[2:].decode("big5", errors="replace")
                    else:
                        try:
                            text = content_bytes.decode("big5")
                        except Exception:
                            text = content_bytes.decode("big5", errors="replace")
                else:
                    try:
                        text = content_bytes.decode("big5")
                    except Exception:
                        text = content_bytes.decode("big5", errors="replace")

                self.items.append(
                    TextItem(
                        index=global_idx,
                        page=page,
                        avatar_id=avatar_id,
                        text=text,
                        is_dialogue=is_dialogue,
                        raw_tail=tail
                    )
                )
                global_idx += 1

    def save(self, target_path: Optional[str] = None):
        """将修改后的文本重新打包并重算各页偏移回写"""
        dst = target_path if target_path else self.file_path

        # 首次保存前自动备份
        if not self.has_backup:
            shutil.copyfile(self.file_path, self.backup_path)

        # 按 page 分组文本对象
        pages_dict: Dict[int, List[TextItem]] = {p: [] for p in range(self.page_count)}
        for item in self.items:
            if item.page in pages_dict:
                pages_dict[item.page].append(item)
            else:
                pages_dict[0].append(item)

        data_offset = self.page_count * 2
        offset_list = []
        body_buf = bytearray()

        for page in range(self.page_count):
            page_items = pages_dict[page]
            offset_list.append(data_offset + len(body_buf))
            for item in page_items:
                raw_item = item.serialize()
                body_buf.extend(raw_item)

        # 构建完整文件：文件头索引 + 数据主体
        out = bytearray()
        for page in range(self.page_count):
            out.extend(struct.pack("<H", offset_list[page]))
        out.extend(body_buf)

        with open(dst, "wb") as fp:
            fp.write(out)

    def restore_from_backup(self):
        """从备份文件还原"""
        if not self.has_backup:
            raise FileNotFoundError(f"未找到可还原的备份文件 ({self.filename}.bak)！")
        shutil.copyfile(self.backup_path, self.file_path)
        self._load()


class SnrManager:
    """游戏目录下所有章节剧本剧情管理器"""

    def __init__(self, game_dir: str):
        self.game_dir = os.path.abspath(game_dir)
        self.chapters: Dict[int, SnrChapter] = {}
        self._detect_chapters()

    def _detect_chapters(self):
        """扫描并加载所有存在的 SnrXm.r3 章节文件"""
        for ch in range(5):
            fname = f"Snr{ch}m.r3"
            target_path = None
            for f in os.listdir(self.game_dir):
                if f.lower() == fname.lower():
                    target_path = os.path.join(self.game_dir, f)
                    break
            if target_path and os.path.isfile(target_path):
                try:
                    self.chapters[ch] = SnrChapter(ch, target_path)
                except Exception as e:
                    print(f"载入章节 {ch} 失败: {e}")

    @property
    def available_chapters(self) -> List[int]:
        return sorted(list(self.chapters.keys()))

    def get_chapter(self, ch_num: int) -> Optional[SnrChapter]:
        return self.chapters.get(ch_num)

    def save_all_chapters(self):
        """保存所有已加载的章节"""
        for chapter in self.chapters.values():
            chapter.save()

    def restore_all_backups(self) -> List[str]:
        """还原所有章节的备份"""
        restored = []
        for chapter in self.chapters.values():
            if chapter.has_backup:
                chapter.restore_from_backup()
                restored.append(chapter.filename)
        return restored

