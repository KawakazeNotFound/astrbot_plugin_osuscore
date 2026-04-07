"""OSU Score 查分插件主文件"""

from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

import asyncio
import tempfile
import os
import time
from io import BytesIO

from .api import OsuApiClient
from .database import Database
from .draw import ScoreImageGenerator
from .utils import parse_command_args, get_mode_name


@register("osuscore", "claude", "OSU查分插件", "0.1.0", "https://github.com/user/astrbot_plugin_osuscore")
class OsuScorePlugin(Star):
    """OSU 查分插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        self.config = config

        # 初始化配置
        self.client_id = config.get("osu_client_id")
        self.client_secret = config.get("osu_client_secret")
        self.db_path = config.get("db_path", "./osuscore.db")

        # 初始化组件
        self.db = Database(self.db_path)
        self.api_client = None
        self.img_generator = ScoreImageGenerator()

        if not self.client_id or not self.client_secret:
            logger.warning("OSU API 凭证未配置，插件功能将不可用")

    async def initialize(self):
        """插件初始化"""
        if self.client_id and self.client_secret:
            self.api_client = OsuApiClient(self.client_id, self.client_secret)
            logger.info("OSU API 客户端初始化成功")

    def _is_api_client_ready(self) -> bool:
        """检查 API 客户端是否可用"""
        return self.api_client is not None

    @filter.command("bind")
    async def bind_account(self, event: AstrMessageEvent):
        """
        绑定 OSU 账号
        使用: /bind <osuid或用户名>
        """
        if not self._is_api_client_ready():
            yield event.plain_result("❌ OSU API 未配置，请检查插件配置")
            return

        user_id = event.get_sender_id()
        args = event.message_str.strip()

        if not args:
            yield event.plain_result("❌ 请输入 OSU 用户 ID 或用户名\n使用: /bind <osuid或用户名>")
            return

        try:
            # 查询用户信息
            user_info = await self.api_client.get_user(args)
            osu_id = user_info["id"]
            osu_name = user_info["username"]

            # 保存到数据库
            await self.db.save_user(user_id, osu_id, osu_name)

            yield event.plain_result(f"✅ 成功绑定账号: {osu_name} (ID: {osu_id})")

        except Exception as e:
            logger.error(f"绑定账号失败: {e}")
            yield event.plain_result(f"❌ 绑定失败: {str(e)}")

    @filter.command("pr")
    async def recent_score(self, event: AstrMessageEvent):
        """
        查询最近成绩
        使用: /pr [用户名] [:模式] [+mods]
        例如: /pr myname :0 +HD
        """
        if not self._is_api_client_ready():
            yield event.plain_result("❌ OSU API 未配置，请检查插件配置")
            return

        user_id = event.get_sender_id()
        message = event.message_str.strip()

        # 解析参数
        args = parse_command_args(message)
        username = args.get("username")
        mode = args.get("mode", "0")

        try:
            # 获取用户信息
            if not username:
                # 使用绑定的账号
                user_data = await self.db.get_user(user_id)
                if not user_data:
                    yield event.plain_result("❌ 未找到绑定的账号，请先使用 /bind 绑定\n使用: /bind <osuid或用户名>")
                    return
                osu_id = user_data["osu_id"]
            else:
                # 查询指定用户
                user_info = await self.api_client.get_user(username)
                osu_id = user_info["id"]

            # 获取最近成绩
            scores = await self.api_client.get_user_scores(
                osu_id,
                mode=self._mode_to_api_format(mode),
                scope="recent",
                limit=1
            )

            if not scores:
                yield event.plain_result("❌ 未找到最近成绩")
                return

            score = scores[0]

            # 获取谱面信息
            beatmap_id = score["beatmap"]["id"]
            beatmap_info = await self.api_client.get_beatmap(beatmap_id)

            # 获取用户完整信息（用于显示）
            user_info = await self.api_client.get_user(osu_id)

            # 生成图片
            score_data = {
                "score": score["score"],
                "accuracy": score["accuracy"],
                "max_combo": score["max_combo"],
                "rank": score["rank"],
                "mods": score["mods"],
                "pp": score.get("pp", 0),
                "created_at": score["created_at"],
                "mode": mode,
            }

            beatmap_data = {
                "title": beatmap_info["beatmapset"]["title"],
                "version": beatmap_info["version"],
                "creator": beatmap_info["beatmapset"]["creator"],
                "difficulty_rating": beatmap_info["difficulty_rating"],
            }

            user_simple = {
                "username": user_info["username"],
            }

            # 生成图片
            img_bytes = await self.img_generator.generate_score_image(
                user_simple,
                score_data,
                beatmap_data
            )

            # 保存到临时文件
            # 注意：文件需要在 yield 后继续存在，所以不立即删除
            os.makedirs("./osuscore_temp", exist_ok=True)
            tmp_path = f"./osuscore_temp/score_{int(time.time() * 1000)}.png"

            with open(tmp_path, "wb") as f:
                f.write(img_bytes.getvalue())

            yield event.image_result(tmp_path)

        except Exception as e:
            logger.error(f"查询最近成绩失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    @filter.command("unbind")
    async def unbind_account(self, event: AstrMessageEvent):
        """
        解绑 OSU 账号
        """
        # 暂时不实现，等后续完善数据库删除功能
        yield event.plain_result("此功能开发中...")

    def _mode_to_api_format(self, mode: str) -> str:
        """将模式转换为 API 格式"""
        mode_map = {
            "0": "osu",
            "1": "taiko",
            "2": "fruits",
            "3": "mania"
        }
        return mode_map.get(mode, "osu")
