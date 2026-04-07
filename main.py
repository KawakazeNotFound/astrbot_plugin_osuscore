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
from .data_adapter import adapt_api_data_for_image
from .pp_calculator import calculate_all_pp_info


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
        # 获取参数（去掉命令名）
        args = event.message_str.strip()
        # 如果消息以 "bind" 开头，去掉它
        if args.lower().startswith("bind"):
            args = args[4:].strip()

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
        # 获取参数（去掉命令名）
        message = event.message_str.strip()
        # 如果消息以 "pr" 开头，去掉它
        if message.lower().startswith("pr"):
            message = message[2:].strip()

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

            logger.info(f"API returned scores: {type(scores)}")
            logger.info(f"Scores data: {scores}")

            if not scores:
                yield event.plain_result("❌ 未找到最近成绩")
                return

            score = scores[0]
            logger.info(f"First score keys: {score.keys() if isinstance(score, dict) else 'not a dict'}")

            # 使用数据适配器转换API数据
            user_info, score_data, beatmap_data = adapt_api_data_for_image(score)
            
            # 如果score响应中没有用户统计信息，额外获取
            if not user_info.get('global_rank') or not user_info.get('country_rank'):
                try:
                    full_user_info = await self.api_client.get_user(str(osu_id))
                    if full_user_info:
                        stats = full_user_info.get('statistics', {})
                        user_info['global_rank'] = stats.get('global_rank', 0)
                        user_info['country_rank'] = stats.get('country_rank', 0)
                        user_info['pp'] = stats.get('pp', 0)
                except Exception as e:
                    logger.warning(f"Failed to get user statistics: {e}")
            
            # 计算PP信息（IF FC, SS PP, PP分解）
            try:
                pp_info = await calculate_all_pp_info(
                    beatmap_id=beatmap_data.get('id'),
                    beatmapset_id=beatmap_data.get('beatmapset_id'),
                    mods=score_data.get('mods', []),
                    accuracy=score_data.get('accuracy', 0),
                    max_combo=score_data.get('max_combo', 0),
                    statistics=score_data.get('statistics', {}),
                    mode=int(score_data.get('mode', 0))
                )
                
                # 将PP信息合并到score_data
                score_data.update(pp_info)
                logger.info(f"PP calculation result: {pp_info}")
            except Exception as e:
                logger.warning(f"Failed to calculate PP: {e}")
            
            logger.info(f"Adapted user_info: {user_info}")
            logger.info(f"Adapted score_data: {score_data}")
            logger.info(f"Adapted beatmap_data: {beatmap_data}")

            # 生成图片
            img_bytes = await self.img_generator.generate_score_image(
                user_info,
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
