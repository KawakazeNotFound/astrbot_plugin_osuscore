import asyncio
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import os

async def main():
    # 模拟从 API 获取的数据
    mock_data = {
        "bg_url": "https://assets.ppy.sh/beatmaps/1010401/covers/cover.jpg",
        "set_id": "1010401",
        "map_id": "2117573",
        "version": "Xandit's Expert",
        "stars": "5.41",
        "star_color": "#FF4E6F",
        "title": "Monster Effect",
        "artist": "THE ORAL CIGARETTES",
        "mapper": "sparxo",
        "time": "1:32",
        "circles": "186",
        "sliders": "259",
        "bpm": "162",
        "assets_dir": f"file://{Path(__file__).parent.resolve()}/assets",
        "cs": "3.8",
        "cs_percent": 38,
        "hp": "5.5",
        "hp_percent": 55,
        "od": "9",
        "od_percent": 90,
        "ar": "9.3",
        "ar_percent": 93,
        "sr_percent": 54.1,
        "avatar_url": "https://a.ppy.sh/2", # 示例头像 peppy
        "user_name": "-Lilac-",
        "is_supporter": True,
        "flag_url": "https://osu.ppy.sh/images/flags/HK.png", # 示例香港区旗
        "country_rank": "3,747",
        "grade": "A",
        "score": "1,247,630",
        "play_time": "2026-04-11 10:20:39",
        "global_rank": "370,567",
        "pp": "84",
        "pp_if_fc": "152",
        "pp_ss": "246",
        "pp_aim": "49",
        "pp_speed": "18",
        "pp_acc": "12",
        "acc": "91.73",
        "max_combo": "168",
        "total_combo": "592",
        "count_300": "375",
        "count_100": "31",
        "count_50": "5",
        "count_miss": "10",
        "pass_count": "4501",
        "play_count": "30403",
        "pass_percent": "15",
        "fail_retry_bars": '<rect x="0" y="2" width="2" height="28" fill="rgba(255, 204, 85, 0.9)" rx="0.5"></rect><rect x="0" y="10" width="2" height="20" fill="rgba(255, 102, 170, 0.9)" rx="0.5"></rect><rect x="4" y="20" width="2" height="10" fill="rgba(255, 204, 85, 0.9)" rx="0.5"></rect><rect x="4" y="25" width="2" height="5" fill="rgba(255, 102, 170, 0.9)" rx="0.5"></rect><rect x="8" y="15" width="2" height="15" fill="rgba(255, 204, 85, 0.9)" rx="0.5"></rect>',
        "rating_avg": "9.47",
        "rating_min": 3,
        "rating_max": 103,
        "rating_negative_percent": 2.8
    }

    # 1. 使用 Jinja2 渲染 HTML
    # 获取模板目录
    template_dir = Path(__file__).parent / "score_templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index.html")
    rendered_html = template.render(**mock_data)

    # 将渲染后的 HTML 临时保存
    temp_html_path = Path(__file__).parent / "temp_render.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    # 2. 使用 Playwright 截图
    print("开始生成测试图片...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 固定视口尺寸
        page = await browser.new_page(viewport={"width": 1100, "height": 700})
        
        # 加载本地生成的 HTML
        await page.goto(f"file://{temp_html_path.resolve()}")
        # 等待字体和图片加载完成（可根据情况调整网络等待）
        await page.wait_for_load_state("networkidle")
        
        # 截图
        output_path = Path(__file__).parent / "test_score_render.png"
        await page.screenshot(path=str(output_path), clip={"x": 0, "y": 0, "width": 1100, "height": 700})
        await browser.close()
        
    print(f"图片生成完毕！保存在: {output_path}")
    
    # 清理临时 HTML
    # os.remove(temp_html_path)

if __name__ == "__main__":
    asyncio.run(main())