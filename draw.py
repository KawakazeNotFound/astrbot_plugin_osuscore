import os
import asyncio
from io import BytesIO
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import numpy as np
import matplotlib as mpl
import matplotlib.colors as mcolors

class StarColorMapper:
    """星级难度颜色映射器"""
    def __init__(self):
        input_values = np.array([0.1, 1.25, 2, 2.5, 3.3, 4.2, 4.9, 5.8, 6.7, 7.7, 9])
        normalized_values = (input_values - np.min(input_values)) / (np.max(input_values) - np.min(input_values))
        colors = [
            "#4290FB", "#4FC0FF", "#4FFFD5", "#7CFF4F", "#F6F05C", 
            "#FF8068", "#FF4E6F", "#C645B8", "#6563DE", "#18158E", "#000000"
        ]
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            "difficultyColourSpectrum", list(zip(normalized_values, colors)), N=16384
        )
        self.norm = mpl.colors.Normalize(vmin=0, vmax=9)
        self.color_arr = mpl.cm.ScalarMappable(norm=self.norm, cmap=self.cmap).to_rgba(
            np.linspace(0, 9, 900), bytes=True
        )
    
    def get_color_hex(self, stars: float) -> str:
        if stars < 0.1:
            return "#AAAAAA"
        elif stars >= 9:
            return "#000000"
        else:
            r, g, b, _a = self.color_arr[int(stars * 100)]
            return f"#{r:02x}{g:02x}{b:02x}"

class ScoreImageGenerator:
    """成绩截图生成器 - 基于 Playwright + HTML"""

    def __init__(self):
        self.template_dir = Path(__file__).parent / "score_templates"
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.star_mapper = StarColorMapper()
        
    async def generate_score_image(
        self,
        user_info: Dict[str, Any],
        score_info: Dict[str, Any],
        beatmap_info: Dict[str, Any]
    ) -> BytesIO:
        """生成成绩截图"""
        stats = score_info.get("statistics", {})
        stars = beatmap_info.get("difficulty_rating", 0.0)
        
        calc_total_combo = (
            beatmap_info.get("count_circles", 0) +
            beatmap_info.get("count_sliders", 0) +
            beatmap_info.get("count_spinners", 0)
        )
        
        total_len = beatmap_info.get("total_length", 0)
        time_str = f"{total_len // 60}:{total_len % 60:02d}"

        acc = score_info.get("accuracy", 0)
        acc_val = acc * 100 if acc <= 1.0 else acc
        
        # 兼容老版数据的 if_fc_pp 或者 pp_if_fc
        pp_if_fc = score_info.get('if_fc_pp', score_info.get('pp_if_fc', 0))
        
        context = {
            "bg_url": f"https://assets.ppy.sh/beatmaps/{beatmap_info.get('beatmapset_id')}/covers/cover.jpg",
            "set_id": str(beatmap_info.get("beatmapset_id", "")),
            "map_id": str(beatmap_info.get("id", "")),
            "version": beatmap_info.get("version", "Normal"),
            "stars": f"{stars:.2f}",
            "star_color": self.star_mapper.get_color_hex(stars),
            "title": beatmap_info.get("title", ""),
            "artist": beatmap_info.get("artist", ""),
            "mapper": beatmap_info.get("creator", ""),
            "time": time_str,
            "circles": str(beatmap_info.get("count_circles", 0)),
            "sliders": str(beatmap_info.get("count_sliders", 0)),
            "bpm": str(beatmap_info.get("bpm", 0)),
            "assets_dir": f"file://{Path(__file__).parent.resolve()}/assets",
            "cs": f"{beatmap_info.get('cs', 0):.1f}",
            "cs_percent": min(100, beatmap_info.get("cs", 0) * 10),
            "hp": f"{beatmap_info.get('hp', 0):.1f}",
            "hp_percent": min(100, beatmap_info.get("hp", 0) * 10),
            "od": f"{beatmap_info.get('od', 0):.1f}",
            "od_percent": min(100, beatmap_info.get("od", 0) * 10),
            "ar": f"{beatmap_info.get('ar', 0):.1f}",
            "ar_percent": min(100, beatmap_info.get("ar", 0) * 10),
            "sr_percent": min(100, (stars / 10.0) * 100),
            "pass_count": min(99999, beatmap_info.get("passcount", 0)),
            "play_count": max(1, beatmap_info.get("playcount", 1)),
            "pass_percent":  f"{(beatmap_info.get('passcount', 0) / max(1, beatmap_info.get('playcount', 1))) * 100:.0f}",
            "fail_retry_bars": self._generate_bar_graph(
                beatmap_info.get("failtimes", {}).get("exit", []),
                beatmap_info.get("failtimes", {}).get("fail", [])
            ),
            "rating_avg": f"{beatmap_info.get('ratings_avg', 0):.2f}" if 'ratings_avg' in beatmap_info else "0.00",
            "rating_min": beatmap_info.get("rating_negative", 0),
            "rating_max": beatmap_info.get("rating_positive", 0),
            "rating_negative_percent": self._calculate_rating_percent(
                beatmap_info.get("rating_negative", 0),
                beatmap_info.get("rating_positive", 0)
            ),
            "avatar_url": user_info.get("avatar_url", ""),
            "user_name": user_info.get("username", ""),
            "is_supporter": user_info.get("is_supporter", False),
            "flag_url": f"https://osu.ppy.sh/images/flags/{user_info.get('country_code', 'XX')}.png",
            "country_rank": f"{user_info.get('country_rank', 0):,}",
            "grade": score_info.get("rank", ""),
            "score": f"{score_info.get('score', 0):,}",
            "play_time": str(score_info.get("created_at", "")).replace("T", " ")[:19],
            "global_rank": f"{user_info.get('global_rank', 0):,}",
            "pp": f"{score_info.get('pp', 0):.0f}" if score_info.get('pp') else "-",
            "pp_if_fc": f"{pp_if_fc:.0f}" if pp_if_fc else "-",
            "pp_ss": f"{score_info.get('ss_pp', 0):.0f}" if score_info.get('ss_pp') else "-",
            "pp_aim": f"{score_info.get('pp_aim', 0):.0f}" if score_info.get('pp_aim') else "0",
            "pp_speed": f"{score_info.get('pp_speed', 0):.0f}" if score_info.get('pp_speed') else "0",
            "pp_acc": f"{score_info.get('pp_acc', 0):.0f}" if score_info.get('pp_acc') else "0",
            "pp_aim_percent": min(100, (score_info.get('pp_aim', 0) / max(1, pp_if_fc)) * 100),
            "pp_speed_percent": min(100, (score_info.get('pp_speed', 0) / max(1, pp_if_fc)) * 100),
            "pp_acc_percent": min(100, (score_info.get('pp_acc', 0) / max(1, pp_if_fc)) * 100),
            "acc": f"{acc_val:.2f}",
            "max_combo": str(score_info.get("max_combo", 0)),
            "total_combo": str(score_info.get("map_max_combo", calc_total_combo) or calc_total_combo),
            "count_300": str(stats.get("count_300", stats.get("great", 0))),
            "count_100": str(stats.get("count_100", stats.get("ok", 0))),
            "count_50": str(stats.get("count_50", stats.get("meh", 0))),
            "count_miss": str(stats.get("count_miss", stats.get("miss", 0))),
        }

        template = self.env.get_template("index.html")
        rendered_html = template.render(**context)
        
        # 将 HTML 保存到临时文件，由于 playwright async_playwright 打开 file://
        temp_html_path = Path(__file__).parent / f"temp_{score_info.get('created_at', 'score').replace(' ', '_').replace(':', '')}.html"
        
        try:
            with open(temp_html_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
                
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1100, "height": 600})
                await page.goto(f"file://{temp_html_path.resolve()}")
                
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception as e:
                    pass # ignore timeout if some images fail to load
                
                img_bytes = await page.screenshot(type="png", clip={"x": 0, "y": 0, "width": 1100, "height": 600})
                await browser.close()
        finally:
            if temp_html_path.exists():
                try:
                    os.remove(temp_html_path)
                except Exception:
                    pass
            
        return BytesIO(img_bytes)

    def _generate_bar_graph(self, retries: list, fails: list) -> str:
        length = max(len(retries), len(fails), 1)
        max_r = max(retries) if retries else 0
        max_f = max(fails) if fails else 0
        max_val = max(max_r, max_f, 1)

        svg_parts = []
        width_step = 100 / length
        
        for i in range(length):
            x = i * width_step
            r_val = retries[i] if i < len(retries) else 0
            f_val = fails[i] if i < len(fails) else 0

            r_h = (r_val / max_val) * 30
            f_h = (f_val / max_val) * 30

            # Draw retry (yellow) and fail (pink) as overlapping rects
            # Normally drawn retry at back, fail on top or vice versa
            if r_h > 0:
                svg_parts.append(f'<rect x="{x:.1f}" y="{30 - r_h:.1f}" width="{width_step * 0.8:.1f}" height="{r_h:.1f}" fill="rgba(255, 204, 85, 0.9)" rx="0.5"></rect>')
            if f_h > 0:
                svg_parts.append(f'<rect x="{x:.1f}" y="{30 - f_h:.1f}" width="{width_step * 0.8:.1f}" height="{f_h:.1f}" fill="rgba(255, 102, 170, 0.9)" rx="0.5"></rect>')

        return "".join(svg_parts)

    def _calculate_rating_percent(self, negative: int, positive: int) -> str:
        """Calculate negative rating percentage. Negative + Positive = 100%"""
        total = negative + positive
        if total == 0:
            return "0"
        percent = (negative / total) * 100
        return f"{percent:.1f}"
