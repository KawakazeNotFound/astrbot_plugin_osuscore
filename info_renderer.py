import base64
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Union

import jinja2
from PIL import UnidentifiedImageError
from playwright.async_api import async_playwright

from .exceptions import NetworkError
from .info_models import Badge, DrawUser
from .utils import FGM, GMN, info_calc


ASSETS_DIR = Path(__file__).parent / "assets"
USER_INFO_BG_DIR = ASSETS_DIR / "cache" / "user"


async def draw_info(
    api_client,
    db,
    uid: Union[int, str],
    mode: str,
    day: int,
    source: str,
    info_bg_urls: list[str],
) -> bytes:
    info = await api_client.get_user_info_data(uid, mode, source)
    statistics = info.statistics
    if not statistics or statistics.play_count == 0:
        raise NetworkError(f"此玩家尚未游玩过{GMN[mode]}模式")

    mode_id = FGM[mode]
    user = await db.get_latest_info_data(info.id, mode_id)
    if user:
        today_date = date.today()
        await db.ensure_today_country_rank(info.id, mode_id, today_date, statistics.country_rank)
        query_date = today_date - timedelta(days=day)
        user = await db.get_info_data_since(info.id, mode_id, query_date)

    if user:
        n_crank = user.get("c_rank")
        n_grank = user.get("g_rank")
        n_pp = user.get("pp")
        n_acc = user.get("acc")
        n_pc = user.get("pc")
        n_count = user.get("count")
        n_ranked_score = user.get("ranked_score")
        n_total_score = user.get("total_score")
        n_xh = user.get("count_xh")
        n_x = user.get("count_x")
        n_sh = user.get("count_sh")
        n_s = user.get("count_s")
        n_a = user.get("count_a")
        n_play_time = user.get("play_time")
        n_badge_count = user.get("badge_count")
    else:
        gc = statistics.grade_counts
        n_crank = statistics.country_rank
        n_grank = statistics.global_rank
        n_pp = statistics.pp
        n_acc = statistics.hit_accuracy
        n_pc = statistics.play_count
        n_count = statistics.total_hits
        n_ranked_score = statistics.ranked_score
        n_total_score = statistics.total_score
        n_xh = gc.ssh
        n_x = gc.ss
        n_sh = gc.sh
        n_s = gc.s
        n_a = gc.a
        n_play_time = statistics.play_time
        n_badge_count = len(info.badges) if info.badges else 0

    bg = await _load_background_base64(api_client, info.id, info_bg_urls)

    if day != 0 and user and user.get("date"):
        day_delta = date.today() - date.fromisoformat(user["date"]) if isinstance(user["date"], str) else date.today() - user["date"]
        footer = datetime.now().strftime("%Y/%m/%d %H:%M:%S") + f" | 数据对比于 {day_delta.days} 天前"
    else:
        footer = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    op, value = info_calc(statistics.pp, n_pp, pp=True)
    pp_change = f"{op}{value:,.2f}" if value != 0 else None

    op, value = info_calc(statistics.global_rank, n_grank, rank=True)
    rank_change = f"{op}{value:,}" if value != 0 else None

    op, value = info_calc(statistics.country_rank, n_crank, rank=True)
    country_rank_change = f"({op}{value:,})" if value != 0 else None

    op, value = info_calc(statistics.hit_accuracy, n_acc)
    acc_change = f"({op}{value:.2f}%)" if value != 0 else None

    def _fmt_change(cur, prev, fmt=",", suffix=""):
        if prev is None:
            return None
        op_, value_ = info_calc(cur, prev)
        return f"({op_}{value_:{fmt}}{suffix})" if value_ != 0 else None

    pc_change = _fmt_change(statistics.play_count, n_pc)
    hits_change = _fmt_change(statistics.total_hits, n_count)
    ranked_score_change = _fmt_change(statistics.ranked_score, n_ranked_score)
    total_score_change = _fmt_change(statistics.total_score, n_total_score)

    gc = statistics.grade_counts
    xh_change = _fmt_change(gc.ssh, n_xh)
    x_change = _fmt_change(gc.ss, n_x)
    sh_change = _fmt_change(gc.sh, n_sh)
    s_change = _fmt_change(gc.s, n_s)
    a_change = _fmt_change(gc.a, n_a)
    play_time_change = _fmt_change(statistics.play_time, n_play_time, suffix="s")

    cur_badge = len(info.badges) if info.badges else 0
    badge_count_change = _fmt_change(cur_badge, n_badge_count)

    badges = [Badge(**i.model_dump()) for i in info.badges] if info.badges else None

    draw_user = DrawUser(
        id=info.id,
        username=info.username,
        country_code=info.country_code,
        mode=mode.upper(),
        badges=badges,
        team=info.team.model_dump() if info.team else None,
        statistics=info.statistics.model_dump() if info.statistics else None,
        footer=footer,
        rank_change=rank_change,
        country_rank_change=country_rank_change,
        pp_change=pp_change,
        acc_change=acc_change,
        pc_change=pc_change,
        hits_change=hits_change,
        ranked_score_change=ranked_score_change,
        total_score_change=total_score_change,
        xh_change=xh_change,
        x_change=x_change,
        sh_change=sh_change,
        s_change=s_change,
        a_change=a_change,
        play_time_change=play_time_change,
        badge_count_change=badge_count_change,
    )

    await db.upsert_info_data(
        osu_id=info.id,
        osu_mode=mode_id,
        date_value=date.today(),
        c_rank=statistics.country_rank,
        g_rank=statistics.global_rank,
        pp=statistics.pp,
        acc=statistics.hit_accuracy,
        pc=statistics.play_count,
        count=statistics.total_hits,
        ranked_score=statistics.ranked_score,
        total_score=statistics.total_score,
        max_combo=statistics.maximum_combo,
        count_xh=gc.ssh,
        count_x=gc.ss,
        count_sh=gc.sh,
        count_s=gc.s,
        count_a=gc.a,
        replays=statistics.replays_watched_by_others,
        play_time=statistics.play_time,
        badge_count=cur_badge,
    )

    template_path = Path(__file__).parent / "info_templates"
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path)), enable_async=True)
    template = template_env.get_template("index.html")
    html = await template.render_async(user_json=draw_user.model_dump_json(), bg=bg)

    return await _render_html_to_jpeg(template_path, html)


async def _render_html_to_jpeg(template_path: Path, html: str) -> bytes:
    temp_html_path = template_path / "_info_render_tmp.html"
    temp_html_path.write_text(html, encoding="utf-8")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = await browser.new_context(viewport={"width": 480, "height": 2000}, device_scale_factor=2)
            page = await context.new_page()
            await page.goto(temp_html_path.as_uri(), wait_until="load")
            elem = await page.query_selector("#display")
            if elem is None:
                raise NetworkError("资料卡模板渲染失败，未找到 #display 元素")
            img = await elem.screenshot(type="jpeg")
            await context.close()
            await browser.close()
            return img
    finally:
        try:
            temp_html_path.unlink(missing_ok=True)
        except OSError:
            pass


async def _load_background_base64(api_client, user_id: int, info_bg_urls: list[str]) -> str:
    bg_path = USER_INFO_BG_DIR / str(user_id) / "info.png"
    if bg_path.exists():
        try:
            encoded_string = base64.b64encode(bg_path.read_bytes()).decode("utf-8")
            return f"data:image/png;base64,{encoded_string}"
        except UnidentifiedImageError:
            bg_path.unlink(missing_ok=True)
            raise NetworkError("自定义背景图片读取错误，请重新上传！")

    urls = [u for u in info_bg_urls if isinstance(u, str) and u.strip()]
    random.shuffle(urls)

    for bg_url in urls:
        try:
            bg_bytes = await api_client.get_image_bytes(bg_url)
            encoded_string = base64.b64encode(bg_bytes).decode("utf-8")
            return f"data:{_guess_image_mime(bg_bytes)};base64,{encoded_string}"
        except Exception:
            continue

    # 远程背景全部失败时，回退到本地素材，避免 /info 直接失败。
    local_fallback = ASSETS_DIR / "convert.jpg"
    if local_fallback.exists():
        encoded_string = base64.b64encode(local_fallback.read_bytes()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded_string}"

    raise NetworkError("背景下载失败: 所有背景地址均不可用")


def _guess_image_mime(content: bytes) -> str:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"
