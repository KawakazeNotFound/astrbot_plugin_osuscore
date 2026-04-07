"""图片生成模块"""

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

try:
    from .utils import format_score_rank, format_accuracy, format_number, get_mode_name, get_mods_string
except ImportError:
    # For direct module loading in tests
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from utils import format_score_rank, format_accuracy, format_number, get_mode_name, get_mods_string


class ScoreImageGenerator:
    """成绩截图生成器"""

    def __init__(self):
        # 图片布局设置
        self.width = 800
        self.height = 600
        self.padding = 20

        # 颜色定义
        self.bg_color = (20, 20, 30)  # 深色背景
        self.text_color = (255, 255, 255)  # 白色文字
        self.accent_color = (30, 215, 230)  # 青色强调色
        self.rank_colors = {
            "XH": (255, 215, 0),  # 金色 SS+
            "X": (255, 215, 0),   # 金色 SS
            "SH": (200, 150, 100), # 银色 S+
            "S": (200, 150, 100),  # 银色 S
            "A": (100, 200, 100),  # 绿色 A
            "B": (100, 150, 200),  # 蓝色 B
            "C": (200, 100, 150),  # 紫色 C
            "D": (200, 100, 100),  # 红色 D
            "F": (100, 100, 100),  # 灰色 F
        }

    def _try_load_font(self, size: int = 20) -> ImageFont.FreeTypeFont:
        """尝试加载系统字体"""
        try:
            # 尝试加载常见的系统字体
            for font_path in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                "/Library/Fonts/Arial.ttf",  # macOS
            ]:
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        except:
            pass

        # 如果没有找到，使用默认字体
        return ImageFont.load_default()

    async def generate_score_image(
        self,
        user_info: Dict[str, Any],
        score_info: Dict[str, Any],
        beatmap_info: Dict[str, Any]
    ) -> BytesIO:
        """
        生成成绩截图
        """
        # 创建图片
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 加载字体
        font_large = self._try_load_font(36)  # 标题
        font_medium = self._try_load_font(24)  # 主要信息
        font_small = self._try_load_font(16)   # 次要信息

        y = self.padding

        # 1. 标题区域 - 谱面信息
        title_text = f"{beatmap_info.get('title', '???')} [{beatmap_info.get('version', '???')}]"
        draw.text((self.padding, y), title_text, font=font_medium, fill=self.text_color)
        y += 40

        # 2. 创作者信息
        creator_text = f"by {beatmap_info.get('creator', '???')}"
        draw.text((self.padding, y), creator_text, font=font_small, fill=(180, 180, 180))
        y += 35

        # 3. 玩家信息
        player_text = f"Player: {user_info.get('username', '???')} ({get_mode_name(score_info.get('mode', '0'))})"
        draw.text((self.padding, y), player_text, font=font_medium, fill=self.accent_color)
        y += 40

        # 4. 成绩分数
        score_value = score_info.get("score", 0)
        score_text = f"Score: {format_number(score_value)}"
        draw.text((self.padding, y), score_text, font=font_large, fill=self.rank_colors.get(score_info.get("rank", "D"), self.text_color))
        y += 50

        # 5. 双线信息区 (准确度, 排名, Combo)
        accuracy = score_info.get("accuracy", 0)
        max_combo = score_info.get("max_combo", 0)
        rank = score_info.get("rank", "D")

        info_y = y
        # 左列信息
        draw.text((self.padding, info_y), "Accuracy:", font=font_small, fill=(180, 180, 180))
        draw.text((self.padding + 150, info_y), format_accuracy(accuracy), font=font_medium, fill=self.text_color)

        info_y += 35
        draw.text((self.padding, info_y), "Combo:", font=font_small, fill=(180, 180, 180))
        draw.text((self.padding + 150, info_y), f"{max_combo}x", font=font_medium, fill=self.text_color)

        # 右列信息
        info_y = y
        rank_display = format_score_rank(rank)
        draw.text((self.width - self.padding - 150, info_y), rank_display, font=font_large, fill=self.rank_colors.get(rank, self.text_color))

        info_y += 35
        pp_text = score_info.get("pp", 0)
        draw.text((self.width - self.padding - 150, info_y), f"{pp_text}pp", font=font_medium, fill=self.text_color)

        y += 80

        # 6. Mod 和谱面难度信息
        mods_text = get_mods_string(score_info.get("mods", []))
        draw.text((self.padding, y), f"Mods: {mods_text}", font=font_small, fill=(180, 180, 180))

        difficulty_text = f"★ {beatmap_info.get('difficulty_rating', 0):.2f}"
        draw.text((self.width - self.padding - 200, y), difficulty_text, font=font_small, fill=self.accent_color)

        y += 40

        # 7. 时间信息
        created_at = score_info.get("created_at", "")
        time_text = f"Submitted: {created_at}"
        draw.text((self.padding, y), time_text, font=font_small, fill=(150, 150, 150))

        # 转换为 BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes
