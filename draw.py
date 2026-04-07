"""图片生成模块 - 基于nonebot-plugin-osubot的实现"""

import os
import asyncio
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, Union
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import matplotlib as mpl
import matplotlib.colors as mcolors
import httpx

try:
    from .utils import format_score_rank, format_accuracy, format_number, get_mode_name, get_mods_string
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from utils import format_score_rank, format_accuracy, format_number, get_mode_name, get_mods_string


# 资源路径
ASSETS_DIR = Path(__file__).parent / "assets"
CACHE_DIR = ASSETS_DIR / "cache"
FONTS_DIR = ASSETS_DIR / "fonts"
MODS_DIR = ASSETS_DIR / "mods"
RANKING_DIR = ASSETS_DIR / "ranking"
WORK_DIR = ASSETS_DIR / "work"

# 确保缓存目录存在
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def draw_fillet(img: Image.Image, radii: int) -> Image.Image:
    """绘制圆角矩形（nonebot实现）
    
    Args:
        img: 原始图片
        radii: 圆角半径
        
    Returns:
        带圆角的图片
    """
    # 画圆（用于分离4个角）
    circle = Image.new("L", (radii * 2, radii * 2), 0)  # 黑色背景画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 白色圆形
    
    # 原图
    img = img.convert("RGBA")
    w, h = img.size
    
    # 画4个角（将整圆分离为4个部分）
    alpha = Image.new("L", img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角
    img.putalpha(alpha)
    return img


class StarColorMapper:
    """星级难度颜色映射器"""
    
    def __init__(self):
        # 参考: https://github.com/ppy/osu-web/blob/master/resources/js/utils/beatmap-helper.ts
        input_values = np.array([0.1, 1.25, 2, 2.5, 3.3, 4.2, 4.9, 5.8, 6.7, 7.7, 9])
        normalized_values = (input_values - np.min(input_values)) / (np.max(input_values) - np.min(input_values))
        
        # 颜色定义（从低到高难度）
        colors = [
            "#4290FB",    # 0.1★ - 蓝色
            "#4FC0FF",    # 1.25★ - 青色
            "#4FFFD5",    # 2★ - 浅青
            "#7CFF4F",    # 2.5★ - 绿色
            "#F6F05C",    # 3.3★ - 黄色
            "#FF8068",    # 4.2★ - 橙色
            "#FF4E6F",    # 4.9★ - 红粉
            "#C645B8",    # 5.8★ - 紫色
            "#6563DE",    # 6.7★ - 靛蓝
            "#18158E",    # 7.7★ - 深靛蓝
            "#000000",    # 9★ - 黑色
        ]
        
        # 创建颜色映射
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            "difficultyColourSpectrum", list(zip(normalized_values, colors)), N=16384
        )
        self.norm = mpl.colors.Normalize(vmin=0, vmax=9)
        self.color_arr = mpl.cm.ScalarMappable(norm=self.norm, cmap=self.cmap).to_rgba(
            np.linspace(0, 9, 900), bytes=True
        )
    
    def get_color(self, stars: float) -> tuple:
        """获取星级对应的RGB颜色"""
        if stars < 0.1:
            return (170, 170, 170)  # 灰色
        elif stars >= 9:
            return (0, 0, 0)  # 黑色
        else:
            r, g, b, _a = self.color_arr[int(stars * 100)]
            return (r, g, b)


class AssetsLoader:
    """资源加载器"""
    
    def __init__(self):
        self.fonts = {}
        self.mod_icons = {}
        self.rank_icons = {}
        self.mode_backgrounds = {}
        self.star_mapper = StarColorMapper()
        self._load_assets()
    
    def _load_assets(self):
        """加载所有资源"""
        try:
            # 加载字体
            self._load_fonts()
            # 加载Mod图标
            self._load_mod_icons()
            # 加载排名图标
            self._load_rank_icons()
            # 加载游戏模式背景
            self._load_mode_backgrounds()
        except Exception as e:
            print(f"Warning: Failed to load some assets: {e}")
    
    def _load_fonts(self):
        """加载字体文件"""
        try:
            # Torus Regular
            torus_regular = FONTS_DIR / "Torus Regular.otf"
            if torus_regular.exists():
                self.fonts['torus_r_15'] = ImageFont.truetype(str(torus_regular), 15)
                self.fonts['torus_r_20'] = ImageFont.truetype(str(torus_regular), 20)
                self.fonts['torus_r_25'] = ImageFont.truetype(str(torus_regular), 25)
                self.fonts['torus_r_30'] = ImageFont.truetype(str(torus_regular), 30)
                self.fonts['torus_r_40'] = ImageFont.truetype(str(torus_regular), 40)
                self.fonts['torus_r_50'] = ImageFont.truetype(str(torus_regular), 50)
                self.fonts['torus_r_60'] = ImageFont.truetype(str(torus_regular), 60)
            
            # Torus SemiBold
            torus_semibold = FONTS_DIR / "Torus SemiBold.otf"
            if torus_semibold.exists():
                self.fonts['torus_sb_15'] = ImageFont.truetype(str(torus_semibold), 15)
                self.fonts['torus_sb_20'] = ImageFont.truetype(str(torus_semibold), 20)
                self.fonts['torus_sb_25'] = ImageFont.truetype(str(torus_semibold), 25)
                self.fonts['torus_sb_30'] = ImageFont.truetype(str(torus_semibold), 30)
                self.fonts['torus_sb_40'] = ImageFont.truetype(str(torus_semibold), 40)
            
            # Venera
            venera = FONTS_DIR / "Venera.otf"
            if venera.exists():
                self.fonts['venera_60'] = ImageFont.truetype(str(venera), 60)
                self.fonts['venera_40'] = ImageFont.truetype(str(venera), 40)
            
            # 如果没有加载到任何字体，使用默认字体
            if not self.fonts:
                default_font = ImageFont.load_default()
                self.fonts['default'] = default_font
        except Exception as e:
            print(f"Warning: Failed to load fonts: {e}")
            self.fonts['default'] = ImageFont.load_default()
    
    def _load_mod_icons(self):
        """加载Mod图标"""
        if MODS_DIR.exists():
            for mod_file in MODS_DIR.glob("*.png"):
                try:
                    self.mod_icons[mod_file.stem] = Image.open(mod_file).convert("RGBA")
                except Exception as e:
                    print(f"Warning: Failed to load mod icon {mod_file.name}: {e}")
    
    def _load_rank_icons(self):
        """加载排名图标"""
        if RANKING_DIR.exists():
            for rank_file in RANKING_DIR.glob("*.png"):
                try:
                    self.rank_icons[rank_file.stem.replace("ranking-", "")] = Image.open(rank_file).convert("RGBA")
                except Exception as e:
                    print(f"Warning: Failed to load rank icon {rank_file.name}: {e}")
    
    def _load_mode_backgrounds(self):
        """加载游戏模式背景"""
        mode_files = {
            "0": "pfm_std.png",      # Standard
            "1": "pfm_taiko.png",    # Taiko
            "2": "pfm_ctb.png",      # Catch
            "3": "pfm_mania.png",    # Mania
        }
        
        for mode, filename in mode_files.items():
            filepath = ASSETS_DIR / filename
            if filepath.exists():
                try:
                    self.mode_backgrounds[mode] = Image.open(filepath).convert("RGBA")
                except Exception as e:
                    print(f"Warning: Failed to load mode background {filename}: {e}")
    
    def get_font(self, name: str, default_size: int = 20):
        """获取字体，如果不存在返回默认字体"""
        if name in self.fonts:
            return self.fonts[name]
        elif 'torus_r_20' in self.fonts:
            return self.fonts['torus_r_20']
        elif 'default' in self.fonts:
            return self.fonts['default']
        else:
            try:
                return ImageFont.truetype("arial.ttf", default_size)
            except:
                return ImageFont.load_default()


# 全局资源加载器
ASSETS = AssetsLoader()


async def download_beatmap_cover(beatmapset_id: int) -> Optional[Image.Image]:
    """
    下载谱面封面图
    尝试多个CDN源，支持缓存
    """
    cache_path = CACHE_DIR / f"cover_{beatmapset_id}.jpg"
    
    # 检查缓存
    if cache_path.exists():
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            cache_path.unlink()
    
    # 多个CDN源
    urls = [
        f"https://assets.ppy.sh/beatmaps/{beatmapset_id}/covers/cover.jpg",
        f"https://b.ppy.sh/thumb/{beatmapset_id}l.jpg",
        f"https://api.nerinyan.moe/bg/{beatmapset_id}",
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content)).convert("RGBA")
                    # 保存到缓存
                    try:
                        img.save(cache_path, "JPEG")
                    except:
                        pass
                    return img
            except Exception:
                continue
    
    return None


async def crop_bg(size: tuple[int, int], img: Image.Image) -> Image.Image:
    """
    智能裁剪背景图以适配目标尺寸
    保持宽高比，居中裁剪
    """
    bg_w, bg_h = img.size
    fix_w, fix_h = size
    
    # 目标宽高比
    fix_scale = fix_h / fix_w
    # 图片宽高比
    bg_scale = bg_h / bg_w
    
    # 图片较高时，缩放至宽度匹配，然后裁剪上下
    if bg_scale > fix_scale:
        scale_width = fix_w / bg_w
        width = int(scale_width * bg_w)
        height = int(scale_width * bg_h)
        sf = img.resize((width, height), Image.Resampling.LANCZOS)
        # 居中裁剪
        crop_height = (height - fix_h) // 2
        crop_img = sf.crop((0, crop_height, width, height - crop_height))
        return crop_img
    # 图片较宽时，缩放至高度匹配，然后裁剪左右
    elif bg_scale < fix_scale:
        scale_height = fix_h / bg_h
        width = int(scale_height * bg_w)
        height = int(scale_height * bg_h)
        sf = img.resize((width, height), Image.Resampling.LANCZOS)
        # 居中裁剪
        crop_width = (width - fix_w) // 2
        crop_img = sf.crop((crop_width, 0, width - crop_width, height))
        return crop_img
    else:
        # 宽高比完全匹配
        return img.resize((fix_w, fix_h), Image.Resampling.LANCZOS)


async def download_user_avatar(avatar_url: str, user_id: int) -> Optional[Image.Image]:
    """下载用户头像
    
    Args:
        avatar_url: 头像URL
        user_id: 用户ID
        
    Returns:
        头像图片对象，失败返回None
    """
    if not avatar_url:
        return None
    
    # 检查缓存
    cache_path = CACHE_DIR / f"avatar_{user_id}.png"
    if cache_path.exists():
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            pass
    
    # 下载头像
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(avatar_url)
            resp.raise_for_status()
            
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            
            # 保存到缓存
            try:
                img.save(cache_path, "PNG")
            except Exception:
                pass
            
            return img
    except Exception as e:
        print(f"Failed to download avatar: {e}")
        return None



def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    anchor: str = "lt",
    outline_width: int = 2
):
    """
    绘制带描边的文字
    提高文字在复杂背景上的可读性
    """
    x, y = position
    
    # 绘制黑色描边（8个方向）
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text(
                    (x + dx, y + dy),
                    text,
                    font=font,
                    anchor=anchor,
                    fill=(0, 0, 0, 255)
                )
    
    # 绘制主文字
    draw.text(position, text, font=font, anchor=anchor, fill=fill)


class ScoreImageGenerator:
    """成绩截图生成器 - 完整nonebot风格实现"""

    def __init__(self):
        # 图片尺寸
        self.width = 1280
        self.height = 720
        self.padding = 30
        
        # 颜色定义
        self.text_color = (255, 255, 255, 255)
        self.text_secondary = (200, 200, 200, 255)
        self.accent_color = (255, 204, 34, 255)  # 金色
        
        # 加载资源
        self.assets = ASSETS
        
    async def generate_score_image(
        self,
        user_info: Dict[str, Any],
        score_info: Dict[str, Any],
        beatmap_info: Dict[str, Any]
    ) -> BytesIO:
        """
        生成成绩截图
        完整的多层合成实现
        """
        try:
            return await self._generate_with_background(user_info, score_info, beatmap_info)
        except Exception as e:
            print(f"Failed to generate with background: {e}, falling back to simple mode")
            return await self._generate_simple(user_info, score_info, beatmap_info)
    
    async def _generate_with_background(
        self,
        user_info: Dict[str, Any],
        score_info: Dict[str, Any],
        beatmap_info: Dict[str, Any]
    ) -> BytesIO:
        """带背景图的完整版本"""
        # 创建画布
        im = Image.new("RGBA", (self.width, self.height))
        draw = ImageDraw.Draw(im)
        
        # 第1层：下载并处理谱面背景
        beatmapset_id = beatmap_info.get("beatmapset_id")
        if beatmapset_id:
            bg_img = await download_beatmap_cover(beatmapset_id)
            if bg_img:
                # 裁剪到合适尺寸
                bg_cropped = await crop_bg((self.width, self.height), bg_img)
                # 应用高斯模糊
                bg_blurred = bg_cropped.filter(ImageFilter.GaussianBlur(10))
                # 降低亮度
                bg_dimmed = ImageEnhance.Brightness(bg_blurred).enhance(0.5)
                # 合成到画布
                im.alpha_composite(bg_dimmed, (0, 0))
        
        # 第2层：游戏模式背景模板
        mode = str(score_info.get("mode", "0"))
        if mode in self.assets.mode_backgrounds:
            mode_bg = self.assets.mode_backgrounds[mode]
            # 如果模板尺寸不匹配，调整大小
            if mode_bg.size != (self.width, self.height):
                mode_bg = mode_bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
            im.alpha_composite(mode_bg, (0, 0))
        
        # 第3层：绘制文本和信息
        await self._draw_score_info(im, draw, user_info, score_info, beatmap_info)
        
        # 第4层：Mod图标
        await self._draw_mod_icons(im, score_info)
        
        # 第5层：排名图标
        await self._draw_rank_icon(im, score_info)
        
        # 第6层：用户头像 (27, 532) 大小170x170，圆角15
        avatar_url = user_info.get('avatar_url')
        user_id = user_info.get('id')
        if avatar_url and user_id:
            try:
                avatar_img = await download_user_avatar(avatar_url, user_id)
                if avatar_img:
                    # 调整大小为170x170
                    avatar_img = avatar_img.resize((170, 170), Image.Resampling.LANCZOS)
                    # 添加圆角
                    avatar_img = draw_fillet(avatar_img, 15)
                    # 合成到主图
                    im.alpha_composite(avatar_img, (27, 532))
            except Exception as e:
                print(f"Failed to composite avatar: {e}")
        
        # 转换为BytesIO
        img_bytes = BytesIO()
        im.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return img_bytes
    
    async def _draw_score_info(
        self,
        im: Image.Image,
        draw: ImageDraw.ImageDraw,
        user_info: Dict[str, Any],
        score_info: Dict[str, Any],
        beatmap_info: Dict[str, Any]
    ):
        """绘制成绩信息文本 - 完全按照nonebot坐标"""
        
        # SetID (32, 25)
        beatmapset_id = beatmap_info.get('beatmapset_id', '???')
        draw.text(
            (32, 25),
            f"Setid：{beatmapset_id}",
            font=self.assets.get_font('torus_sb_20'),
            anchor="lm",
            fill=(255, 255, 255, 255)
        )
        
        # MapID (650, 25) - 右对齐
        map_id = beatmap_info.get('id', beatmap_info.get('beatmap_id', '???'))
        draw.text(
            (650, 25),
            f"Mapid: {map_id}",
            font=self.assets.get_font('torus_sb_20'),
            anchor="rm",
            fill=(255, 255, 255, 255)
        )
        
        # 谱面版本 (65, 80) - 在模式图标右侧
        version = beatmap_info.get('version', '???')
        draw_text_with_outline(
            draw,
            (65, 80),
            version,
            self.assets.get_font('torus_sb_15'),
            fill=(255, 255, 255, 255),
            anchor="lm"
        )
        
        # 谱面标题 (30, 200)
        title = beatmap_info.get('title', '???')
        draw_text_with_outline(
            draw,
            (30, 200),
            title,
            self.assets.get_font('torus_sb_30'),
            fill=(255, 255, 255, 255),
            anchor="lm"
        )
        
        # 艺术家 (30, 230)
        # 如果有artist字段用artist，否则用beatmapset.artist，都没有就用creator
        artist = beatmap_info.get('artist')
        if not artist:
            beatmapset = beatmap_info.get('beatmapset', {})
            artist = beatmapset.get('artist', beatmap_info.get('creator', '???'))
        
        draw_text_with_outline(
            draw,
            (30, 230),
            artist,
            self.assets.get_font('torus_sb_20'),
            fill=(255, 255, 255, 255),
            anchor="lm"
        )
        
        # 谱师 (30, 265)
        creator = beatmap_info.get('creator', '???')
        mapper_text = f"谱师: {creator}"
        draw_text_with_outline(
            draw,
            (30, 265),
            mapper_text,
            self.assets.get_font('torus_sb_15'),
            fill=(255, 255, 255, 255),
            anchor="lm"
        )
        
        # 星级 (556, 85)
        difficulty = beatmap_info.get("difficulty_rating", 0)
        if difficulty < 6.5:
            star_color = (0, 0, 0, 255)
        else:
            star_color = (255, 217, 102, 255)
        
        draw.text(
            (556, 85),
            f"★{difficulty:.2f}",
            font=self.assets.get_font('torus_sb_20'),
            anchor="lm",
            fill=star_color
        )
        
        # 评价/排名 (772, 185) - 使用Venera字体
        rank = score_info.get("rank", "F")
        draw.text(
            (772, 185),
            rank,
            font=self.assets.get_font('venera_60'),
            anchor="mm",
            fill=(255, 255, 255, 255)
        )
        
        # 分数 (880, 165)
        score_value = score_info.get("score", 0)
        draw.text(
            (880, 165),
            f"{score_value:,}",
            font=self.assets.get_font('torus_r_60'),
            anchor="lm",
            fill=(255, 255, 255, 255)
        )
        
        # 达成时间标签 (883, 230)
        draw.text(
            (883, 230),
            "达成时间：",
            font=self.assets.get_font('torus_sb_20'),
            anchor="lm",
            fill=(255, 255, 255, 255)
        )
        
        # 达成时间值 (985, 230)
        created_at = score_info.get("created_at", "")
        if created_at:
            draw.text(
                (985, 230),
                created_at,
                font=self.assets.get_font('torus_sb_20'),
                anchor="lm",
                fill=(255, 255, 255, 255)
            )
        
        # 玩家名 (208, 550)
        draw.text(
            (208, 550),
            user_info.get('username', '???'),
            font=self.assets.get_font('torus_sb_30'),
            anchor="lm",
            fill=(255, 255, 255, 255)
        )
        
        # 全球排名 - 标签在(883, 260)，数值在(985, 260)
        global_rank = user_info.get('global_rank')
        if global_rank and global_rank > 0:
            draw.text(
                (883, 260),
                "全球排行：",
                font=self.assets.get_font('torus_sb_20'),
                anchor="lm",
                fill=(255, 255, 255, 255)
            )
            draw.text(
                (985, 260),
                f"#{global_rank:,}",  # 使用逗号分隔千位
                font=self.assets.get_font('torus_sb_25'),
                anchor="lm",
                fill=(255, 255, 255, 255)
            )
        
        # 地区排名 (283, 630)
        country_rank = user_info.get('country_rank')
        if country_rank and country_rank > 0:
            draw.text(
                (283, 630),
                f"#{country_rank:,}",  # 使用逗号分隔千位
                font=self.assets.get_font('torus_sb_25'),
                anchor="lm",
                fill=(255, 255, 255, 255)
            )
        
        # PP值 (768, 438) - 所有模式统一位置
        pp_value = score_info.get("pp", 0)
        draw.text(
            (768, 438),
            f"{pp_value:.0f}",
            font=self.assets.get_font('torus_r_50'),
            anchor="mm",
            fill=(255, 255, 255, 255)
        )
        
        # 获取游戏模式
        mode = str(score_info.get('mode', '0'))
        
        # Standard模式显示PP分解和IF/SS PP
        if mode == '0':
            # IF FC PP (933, 393)
            if_fc_pp = score_info.get('if_fc_pp', 0)
            if if_fc_pp > 0:
                draw.text(
                    (933, 393),
                    f"{if_fc_pp:.0f}",
                    font=self.assets.get_font('torus_r_25'),
                    anchor="mm",
                    fill=(255, 255, 255, 255)
                )
            
            # SS PP (1066, 393)
            ss_pp = score_info.get('ss_pp', 0)
            if ss_pp > 0:
                draw.text(
                    (1066, 393),
                    f"{ss_pp:.0f}",
                    font=self.assets.get_font('torus_r_25'),
                    anchor="mm",
                    fill=(255, 255, 255, 255)
                )
            
            # AIM PP (933, 482)
            pp_aim = score_info.get('pp_aim', 0)
            if pp_aim > 0:
                draw.text(
                    (933, 482),
                    f"{pp_aim:.0f}",
                    font=self.assets.get_font('torus_r_25'),
                    anchor="mm",
                    fill=(255, 255, 255, 255)
                )
            
            # SPEED PP (1066, 482)
            pp_speed = score_info.get('pp_speed', 0)
            if pp_speed > 0:
                draw.text(
                    (1066, 482),
                    f"{pp_speed:.0f}",
                    font=self.assets.get_font('torus_r_25'),
                    anchor="mm",
                    fill=(255, 255, 255, 255)
                )
            
            # ACC PP (1200, 482)
            pp_acc = score_info.get('pp_acc', 0)
            if pp_acc > 0:
                draw.text(
                    (1200, 482),
                    f"{pp_acc:.0f}",
                    font=self.assets.get_font('torus_r_25'),
                    anchor="mm",
                    fill=(255, 255, 255, 255)
                )
        
        # 准确率 (768, 577) - 所有模式统一位置
        accuracy = score_info.get("accuracy", 0) * 100
        draw.text(
            (768, 577),
            f"{accuracy:.2f}%",
            font=self.assets.get_font('torus_r_25'),
            anchor="mm",
            fill=(255, 255, 255, 255)
        )
        
        # Combo (768, 666) - 所有模式统一位置
        max_combo = score_info.get("max_combo", 0)
        draw.text(
            (768, 666),
            f"{max_combo:,}",
            font=self.assets.get_font('torus_r_25'),
            anchor="mm",
            fill=(255, 255, 255, 255)
        )
        
        # Standard模式的300/100/50/Miss (933, 577), (1066, 577), (933, 666), (1066, 666)
        if mode == '0':
            stats = score_info.get("statistics", {})
            # 300 (933, 577)
            draw.text(
                (933, 577),
                f"{stats.get('count_300', 0)}",
                font=self.assets.get_font('torus_r_25'),
                anchor="mm",
                fill=(255, 255, 255, 255)
            )
            # 100 (1066, 577)
            draw.text(
                (1066, 577),
                f"{stats.get('count_100', 0)}",
                font=self.assets.get_font('torus_r_25'),
                anchor="mm",
                fill=(255, 255, 255, 255)
            )
            # 50 (933, 666)
            draw.text(
                (933, 666),
                f"{stats.get('count_50', 0)}",
                font=self.assets.get_font('torus_r_25'),
                anchor="mm",
                fill=(255, 255, 255, 255)
            )
            # MISS (1066, 666)
            draw.text(
                (1066, 666),
                f"{stats.get('count_miss', 0)}",
                font=self.assets.get_font('torus_r_25'),
                anchor="mm",
                fill=(255, 68, 111, 255)  # 红色
            )
            
        # ============== 新增：绘制左侧 Map Stats (CS, HP, OD, AR, SR) ==============
        # 数据获取
        cs = beatmap_info.get("cs", 0)
        hp = beatmap_info.get("drain", 0)
        od = beatmap_info.get("accuracy", 0)
        ar = beatmap_info.get("ar", 0)
        sr = beatmap_info.get("difficulty_rating", 0)
        
        map_stats = [cs, hp, od, ar]
        for num, val in enumerate(map_stats):
            # 将0-10的属性值映射到最大长度400
            difflen = int(400 * max(0, val) / 10) if val <= 10 else 400
            if difflen > 0:
                diff_len_img = Image.new("RGBA", (difflen, 8), (255, 255, 255, 255))
                im.alpha_composite(diff_len_img, (165, 352 + 35 * num))
            
            # 绘制属性数值 (610, 355 + 35 * num)
            text_val = f"{val:.0f}" if val == round(val) else (f"{val:.2f}" if val != round(val, 1) else f"{val:.1f}")
            draw.text(
                (610, 355 + 35 * num),
                text_val,
                font=self.assets.get_font('torus_sb_20'),
                anchor="mm",
                fill=(255, 255, 255, 255)
            )
            
        # 绘制 SR (490)
        sr_difflen = int(400 * max(0.0, sr) / 10) if sr <= 10 else 400
        if sr_difflen > 0:
            sr_diff_len_img = Image.new("RGBA", (sr_difflen, 8), (255, 255, 255, 255))
            im.alpha_composite(sr_diff_len_img, (165, 490))
        
        draw.text(
            (610, 493),
            f"{sr:.2f}",
            font=self.assets.get_font('torus_sb_20'),
            anchor="mm",
            fill=(255, 255, 255, 255)
        )
    
    async def _draw_mod_icons(self, im: Image.Image, score_info: Dict[str, Any]):
        """绘制Mod图标 - 按照nonebot坐标 (880 + 50*n, 100)"""
        mods = score_info.get("mods", [])
        if not mods:
            return
        
        for idx, mod in enumerate(mods):
            mod_name = mod if isinstance(mod, str) else mod.get("acronym", "")
            
            if mod_name in self.assets.mod_icons:
                mod_icon = self.assets.mod_icons[mod_name]
                # nonebot使用原始尺寸，不调整大小
                # 位置：x = 880 + 50 * idx, y = 100
                x = 880 + 50 * idx
                y = 100
                im.alpha_composite(mod_icon, (x, y))
    
    async def _draw_rank_icon(self, im: Image.Image, score_info: Dict[str, Any]):
        """绘制排名图标 - 不显示大图标，nonebot在(772, 185)位置用文字"""
        # nonebot使用Venera字体直接绘制排名文字，不是图标
        # 所以这个函数不需要做任何事，文字已经在_draw_score_info中绘制
        pass
    
    async def _generate_simple(
        self,
        user_info: Dict[str, Any],
        score_info: Dict[str, Any],
        beatmap_info: Dict[str, Any]
    ) -> BytesIO:
        """简单模式（降级方案）"""
        # 创建纯色背景
        img = Image.new("RGB", (self.width, self.height), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        font_large = self.assets.get_font('torus_sb_30')
        font_medium = self.assets.get_font('torus_r_20')
        font_small = self.assets.get_font('torus_r_15')
        
        y = self.padding
        
        # 谱面信息
        title_text = f"{beatmap_info.get('title', '???')} [{beatmap_info.get('version', '???')}]"
        draw.text((self.padding, y), title_text, font=font_medium, fill=(255, 255, 255))
        y += 40
        
        creator_text = f"by {beatmap_info.get('creator', '???')}"
        draw.text((self.padding, y), creator_text, font=font_small, fill=(180, 180, 180))
        y += 35
        
        # 玩家信息
        player_text = f"Player: {user_info.get('username', '???')}"
        draw.text((self.padding, y), player_text, font=font_medium, fill=(30, 215, 230))
        y += 40
        
        # 成绩
        score_value = score_info.get("score", 0)
        score_text = f"Score: {format_number(score_value)}"
        draw.text((self.padding, y), score_text, font=font_large, fill=(255, 255, 255))
        y += 50
        
        # 详细信息
        accuracy = score_info.get("accuracy", 0)
        max_combo = score_info.get("max_combo", 0)
        rank = score_info.get("rank", "D")
        
        draw.text((self.padding, y), f"Accuracy: {format_accuracy(accuracy)}", font=font_medium, fill=(255, 255, 255))
        y += 35
        draw.text((self.padding, y), f"Combo: {max_combo}x", font=font_medium, fill=(255, 255, 255))
        y += 35
        draw.text((self.padding, y), f"Rank: {rank}", font=font_medium, fill=(255, 255, 255))
        
        # 转换为BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return img_bytes
