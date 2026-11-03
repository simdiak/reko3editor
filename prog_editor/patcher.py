"""
《三国志英杰传》游戏目录与主程序补丁管理器
负责定位 Main.exe、Bakdata.r3、Snr*m.r3、Snr*d.r3、状态检测、二进制读写与备份还原
"""

import os
import shutil
from typing import Dict, Optional, Tuple, List
from prog_editor.patches import ALL_PATCHES, Patch
from prog_editor.bakdata import BakdataManager
from prog_editor.snr_manager import SnrManager
from prog_editor.snrd_manager import SnrdManager


class GamePatcher:
    """游戏主程序、武将基础数据、剧情文本及剧本事件指令补丁执行器"""

    EXPECTED_EXE_SIZE = 246517  # 原版 Main.exe 文件大小

    def __init__(self, game_dir: str):
        self.game_dir = os.path.abspath(game_dir)
        self.exe_path: Optional[str] = None
        self.raw_data: bytearray = bytearray()
        self.bak_manager: Optional[BakdataManager] = None
        self.snr_manager: Optional[SnrManager] = None
        self.snrd_manager: Optional[SnrdManager] = None
        self._validate_and_load()

    def _validate_and_load(self):
        """校验目录中是否存在 Main.exe 并加载数据，同时探测各类数据文件"""
        if not os.path.isdir(self.game_dir):
            raise ValueError(f"指定的路径不是一个有效的目录:\n{self.game_dir}")

        # 1. 查找 Main.exe (大小写不敏感)
        target_exe = None
        target_bak = None
        for filename in os.listdir(self.game_dir):
            lower = filename.lower()
            if lower == "main.exe":
                target_exe = filename
            elif lower == "bakdata.r3":
                target_bak = filename

        if not target_exe:
            raise FileNotFoundError(
                f"在所选目录下未找到游戏主程序 Main.exe！\n"
                f"当前目录: {self.game_dir}\n"
                f"请确保选择的是包含 Main.exe 的《三国志英杰传》游戏根目录。"
            )

        self.exe_path = os.path.join(self.game_dir, target_exe)

        with open(self.exe_path, 'rb') as f:
            data = f.read()

        if len(data) < 2 or data[:2] != b"MZ":
            raise ValueError(
                f"文件 {target_exe} 不是合法的 DOS 可执行程序 (缺少 MZ 标志)！"
            )

        self.raw_data = bytearray(data)

        # 2. 如果存在 Bakdata.r3，加载武将三项能力
        if target_bak:
            bak_path = os.path.join(self.game_dir, target_bak)
            try:
                self.bak_manager = BakdataManager(bak_path)
            except Exception as e:
                print(f"载入 Bakdata.r3 发生警告: {e}")
                self.bak_manager = None
        else:
            self.bak_manager = None

        # 3. 加载剧情对白剧本管理器 (Snr0m.r3 ~ Snr4m.r3)
        try:
            self.snr_manager = SnrManager(self.game_dir)
        except Exception as e:
            print(f"初始化 SnrManager 发生警告: {e}")
            self.snr_manager = None

        # 4. 加载剧本事件与战斗指令管理器 (Snr0d.r3 ~ Snr4d.r3)
        try:
            self.snrd_manager = SnrdManager(self.game_dir)
        except Exception as e:
            print(f"初始化 SnrdManager 发生警告: {e}")
            self.snrd_manager = None

    @property
    def backup_path(self) -> str:
        """主程序备份文件路径"""
        return f"{self.exe_path}.bak"

    @property
    def has_backup(self) -> bool:
        """是否存在原始备份文件"""
        return os.path.isfile(self.backup_path)

    @property
    def has_bakdata(self) -> bool:
        """是否成功载入了 Bakdata.r3"""
        return self.bak_manager is not None

    @property
    def has_snr(self) -> bool:
        """是否成功探测到章节剧情文本文件"""
        return self.snr_manager is not None and len(self.snr_manager.available_chapters) > 0

    @property
    def has_snrd(self) -> bool:
        """是否成功探测到章节剧本指令文件"""
        return self.snrd_manager is not None and len(self.snrd_manager.available_chapters) > 0

    def get_patch_states(self) -> Dict[str, bool]:
        """获取所有可用补丁在当前文件的开关状态"""
        states = {}
        for p in ALL_PATCHES:
            states[p.patch_id] = p.is_enabled(self.raw_data)
        return states

    def apply_and_save(
        self,
        desired_states: Dict[str, bool],
        save_bakdata: bool = True,
        save_snr: bool = True,
        save_snrd: bool = True
    ):
        """应用用户勾选的补丁状态并写回 Main.exe，同时保存 Bakdata.r3、剧情对白与剧本指令"""
        if not self.exe_path:
            raise ValueError("主程序尚未正确载入！")

        # 1. 保存 Main.exe 补丁
        if not self.has_backup:
            shutil.copyfile(self.exe_path, self.backup_path)

        for p in ALL_PATCHES:
            should_enable = desired_states.get(p.patch_id, False)
            if should_enable:
                p.apply(self.raw_data)
            else:
                p.revert(self.raw_data)

        with open(self.exe_path, 'wb') as f:
            f.write(self.raw_data)

        # 2. 保存 Bakdata.r3 武将三项能力
        if save_bakdata and self.bak_manager:
            self.bak_manager.save()

        # 3. 保存剧情章节文本 (SNRM)
        if save_snr and self.snr_manager:
            self.snr_manager.save_all_chapters()

        # 4. 保存剧本事件指令 (SNRD)
        if save_snrd and self.snrd_manager:
            self.snrd_manager.save_all_chapters()

    def restore_from_backup(self) -> List[str]:
        """从 .bak 备份文件还原原版文件"""
        restored_items = []
        if self.has_backup:
            shutil.copyfile(self.backup_path, self.exe_path)
            with open(self.exe_path, 'rb') as f:
                self.raw_data = bytearray(f.read())
            restored_items.append("Main.exe")

        if self.bak_manager and self.bak_manager.has_backup:
            self.bak_manager.restore_from_backup()
            restored_items.append("Bakdata.r3")

        if self.snr_manager:
            restored_snr = self.snr_manager.restore_all_backups()
            restored_items.extend(restored_snr)

        if self.snrd_manager:
            restored_snrd = self.snrd_manager.restore_all_backups()
            restored_items.extend(restored_snrd)

        if not restored_items:
            raise FileNotFoundError("未找到可供还原的备份文件 (.bak)！")

        return restored_items
