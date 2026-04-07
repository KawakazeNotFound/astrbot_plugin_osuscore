"""OSU Score 查分插件主文件"""

import os
import re
import time

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

from .api import OsuApiClient
from .database import Database
from .draw import ScoreImageGenerator
from .exceptions import NetworkError
from .info_renderer import draw_info
from .utils import parse_command_args, parse_mania_command_args, NGM
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
        self.info_bg = config.get(
            "info_bg",
            [
                "https://t.alcy.cc/mp",
                "https://t.alcy.cc/moemp",
                "https://picsum.photos/1280/720",
            ],
        )

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
        assert self.api_client is not None

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

            old_user = await self.db.get_user(user_id)
            osu_mode = int(old_user["osu_mode"]) if old_user and "osu_mode" in old_user else 0

            # 保存到数据库
            await self.db.save_user(user_id, osu_id, osu_name, osu_mode)

            yield event.plain_result(f"✅ 成功绑定账号: {osu_name} (ID: {osu_id})")

        except Exception as e:
            logger.error(f"绑定账号失败: {e}")
            yield event.plain_result(f"❌ 绑定失败: {str(e)}")

    @filter.command("sbbind")
    async def bind_sb_account(self, event: AstrMessageEvent):
        """
        绑定 SB 服务器账号
        使用: /sbbind <用户名>
        """
        if not self._is_api_client_ready():
            yield event.plain_result("❌ OSU API 未配置，请检查插件配置")
            return
        assert self.api_client is not None

        user_id = event.get_sender_id()
        args = event.message_str.strip()
        if args.lower().startswith("sbbind"):
            args = args[6:].strip()

        if not args:
            yield event.plain_result("❌ 请输入 SB 服务器用户名\n使用: /sbbind <用户名>")
            return

        try:
            old_sb_user = await self.db.get_sb_user(user_id)
            if old_sb_user:
                yield event.plain_result(f"您已绑定{old_sb_user['osu_name']}，如需要解绑请输入 /sbunbind")
                return

            sb_uid = await self.api_client.get_uid_by_name(args, "ppysb")
            await self.db.save_sb_user(user_id, sb_uid, args)
            yield event.plain_result(f"✅ 成功绑定 ppysb 服务器用户：{args}")
        except NetworkError:
            yield event.plain_result(f"❌ 绑定失败，找不到叫 {args} 的人哦")
        except Exception as e:
            logger.error(f"绑定 SB 账号失败: {e}")
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
        assert self.api_client is not None

        user_id = event.get_sender_id()
        # 获取参数（去掉命令名）
        message = event.message_str.strip()
        # 如果消息以 "pr" 开头，去掉它
        if message.lower().startswith("pr"):
            message = message[2:].strip()

        # 解析参数
        args = parse_command_args(message)
        username = args.get("username")
        mode = args.get("mode")

        bound_user_data = await self.db.get_user(user_id)
        if not args.get("mode_specified"):
            mode = str(bound_user_data["osu_mode"]) if bound_user_data else "0"
        if mode is None:
            mode = "0"
        mode_api = self._mode_to_api_format(mode)

        try:
            # 获取用户信息
            if not username:
                # 使用绑定的账号
                user_data = bound_user_data
                if not user_data:
                    yield event.plain_result("❌ 未找到绑定的账号，请先使用 /bind 绑定\n使用: /bind <osuid或用户名>")
                    return
                osu_id = user_data["osu_id"]
            else:
                # 查询指定用户
                user_info = await self.api_client.get_user(username, mode=mode_api)
                osu_id = user_info["id"]

            # 获取最近成绩
            scores = await self.api_client.get_user_scores(
                osu_id,
                mode=mode_api,
                scope="recent",
                limit=1,
                include_failed=False,
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
                    full_user_info = await self.api_client.get_user(str(osu_id), mode=mode_api)
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

    @filter.command("info")
    async def user_info(self, event: AstrMessageEvent):
        """
        查询个人资料卡
        使用: /info [用户名] [:模式] [#天数] [&服务器]
        """
        if not self._is_api_client_ready():
            yield event.plain_result("❌ OSU API 未配置，请检查插件配置")
            return
        assert self.api_client is not None

        user_id = event.get_sender_id()
        message = event.message_str.strip()
        if message.lower().startswith("info"):
            message = message[4:].strip()

        state = await self._parse_info_state(user_id, message)
        if "error" in state:
            yield event.plain_result(state["error"])
            return

        try:
            data = await draw_info(
                self.api_client,
                self.db,
                state["user"],
                NGM[state["mode"]],
                state["day"],
                state["source"],
                self.info_bg,
            )

            os.makedirs("./osuscore_temp", exist_ok=True)
            tmp_path = f"./osuscore_temp/info_{int(time.time() * 1000)}.jpg"
            with open(tmp_path, "wb") as f:
                f.write(data)

            yield event.image_result(tmp_path)
        except NetworkError as e:
            yield event.plain_result(
                f"在查找用户：{state['username']} {NGM[state['mode']]}模式 {state['day']}日内 成绩时{str(e)}"
            )
        except Exception as e:
            logger.error(f"查询用户资料失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    @filter.command("mania")
    async def mania_score(self, event: AstrMessageEvent):
        """查询 osu!mania 成绩。

        使用:
            /mania [用户名] [recent|best] [数量] [4k|7k] [+mods]

        示例:
            /mania
            /mania peppy best 3
            /mania peppy recent 1 4k
            /mania peppy best 5 +HD
        """
        if not self._is_api_client_ready():
            yield event.plain_result("❌ OSU API 未配置，请检查插件配置")
            return
        assert self.api_client is not None

        user_id = event.get_sender_id()
        message = event.message_str.strip()
        if message.lower().startswith("mania"):
            message = message[5:].strip()

        args = parse_mania_command_args(message)
        username = args.get("username")
        scope = args.get("scope", "recent")
        limit = int(args.get("limit", 1))
        variant = args.get("variant")
        required_mods = args.get("mods", [])

        bound_user_data = await self.db.get_user(user_id)

        try:
            if not username:
                if not bound_user_data:
                    yield event.plain_result("❌ 未找到绑定的账号，请先使用 /bind 绑定\n使用: /bind <osuid或用户名>")
                    return
                osu_id = int(bound_user_data["osu_id"])
                username = str(bound_user_data.get("osu_name", ""))
                mania_user_info = await self.api_client.get_user(str(osu_id), mode="mania")
            else:
                mania_user_info = await self.api_client.get_user(username, mode="mania")
                osu_id = int(mania_user_info["id"])

            # 有 mod 过滤时扩大拉取窗口，提升命中率。
            fetch_limit = min(50, max(limit, limit * 5 if required_mods else limit))
            scores = await self.api_client.get_user_scores(
                osu_id,
                mode="mania",
                scope=scope,
                limit=fetch_limit,
                include_failed=False,
            )

            if required_mods:
                scores = [s for s in scores if self._score_has_mods(s, required_mods)]

            if not scores:
                if required_mods:
                    yield event.plain_result(
                        f"❌ 未找到满足 +{''.join(required_mods)} 的 mania {scope} 成绩"
                    )
                else:
                    yield event.plain_result(f"❌ 未找到 mania {scope} 成绩")
                return

            selected_scores = scores[:limit]
            variant_summary = self._format_mania_variant_summary(mania_user_info, variant)
            if variant_summary:
                yield event.plain_result(variant_summary)

            if limit > 5:
                yield event.plain_result("⚠️ 为避免刷屏，mania 单次最多发送前 5 条图片结果")
                selected_scores = selected_scores[:5]

            stats = mania_user_info.get("statistics", {})

            for index, score in enumerate(selected_scores, start=1):
                user_info, score_data, beatmap_data = adapt_api_data_for_image(score)

                user_info["global_rank"] = stats.get("global_rank", user_info.get("global_rank", 0))
                user_info["country_rank"] = stats.get("country_rank", user_info.get("country_rank", 0))
                user_info["pp"] = stats.get("pp", user_info.get("pp", 0))

                # 对 mania 使用官方 attributes 接口补全模式难度属性。
                try:
                    attr_resp = await self.api_client.get_beatmap_attributes(
                        beatmap_id=int(beatmap_data.get("id") or beatmap_data.get("beatmap_id") or 0),
                        mods=score_data.get("mods", []),
                        ruleset="mania",
                    )
                    attributes = attr_resp.get("attributes", {}) if isinstance(attr_resp, dict) else {}
                    if attributes.get("star_rating"):
                        beatmap_data["difficulty_rating"] = attributes.get("star_rating")
                    if attributes.get("max_combo"):
                        score_data["map_max_combo"] = attributes.get("max_combo")
                except Exception as e:
                    logger.warning(f"Failed to fetch mania beatmap attributes: {e}")

                try:
                    pp_info = await calculate_all_pp_info(
                        beatmap_id=beatmap_data.get("id"),
                        beatmapset_id=beatmap_data.get("beatmapset_id"),
                        mods=score_data.get("mods", []),
                        accuracy=score_data.get("accuracy", 0),
                        max_combo=score_data.get("max_combo", 0),
                        statistics=score_data.get("statistics", {}),
                        mode=int(score_data.get("mode", 3)),
                    )
                    score_data.update(pp_info)
                except Exception as e:
                    logger.warning(f"Failed to calculate mania PP: {e}")

                img_bytes = await self.img_generator.generate_score_image(
                    user_info,
                    score_data,
                    beatmap_data,
                )

                os.makedirs("./osuscore_temp", exist_ok=True)
                tmp_path = f"./osuscore_temp/mania_{int(time.time() * 1000)}_{index}.png"
                with open(tmp_path, "wb") as f:
                    f.write(img_bytes.getvalue())

                yield event.image_result(tmp_path)

        except Exception as e:
            logger.error(f"查询 mania 成绩失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    @filter.command("unbind")
    async def unbind_account(self, event: AstrMessageEvent):
        """
        解绑 OSU 账号
        """
        user_id = event.get_sender_id()
        user_data = await self.db.get_user(user_id)
        if not user_data:
            yield event.plain_result("尚未绑定，无需解绑")
            return
        await self.db.delete_user(user_id)
        yield event.plain_result("✅ 解绑成功！")

    @filter.command("sbunbind")
    async def unbind_sb_account(self, event: AstrMessageEvent):
        """
        解绑 SB 服务器账号
        """
        user_id = event.get_sender_id()
        sb_user = await self.db.get_sb_user(user_id)
        if not sb_user:
            yield event.plain_result("尚未绑定，无需解绑")
            return
        await self.db.delete_sb_user(user_id)
        yield event.plain_result("✅ 解绑成功！")

    def _mode_to_api_format(self, mode: str) -> str:
        """将模式转换为 API 格式"""
        mode_map = {
            "0": "osu",
            "1": "taiko",
            "2": "fruits",
            "3": "mania"
        }
        return mode_map.get(mode, "osu")

    def _score_has_mods(self, score: dict, required_mods: list[str]) -> bool:
        """检查成绩是否包含目标 mods（子集匹配）。"""
        if not required_mods:
            return True

        score_mods = {
            str(mod.get("acronym", "")).upper()
            for mod in score.get("mods", [])
            if isinstance(mod, dict)
        }
        return set(m.upper() for m in required_mods).issubset(score_mods)

    def _format_mania_variant_summary(self, mania_user_info: dict, variant: str | None) -> str | None:
        """格式化 mania 变体信息（4k/7k）。"""
        if not variant:
            return None

        statistics = mania_user_info.get("statistics", {})
        variants = statistics.get("variants") or []
        for item in variants:
            if not isinstance(item, dict):
                continue
            if str(item.get("variant", "")).lower() != variant.lower():
                continue

            pp = float(item.get("pp") or 0)
            global_rank = item.get("global_rank")
            country_rank = item.get("country_rank")
            gr = f"#{global_rank:,}" if isinstance(global_rank, int) and global_rank > 0 else "-"
            cr = f"#{country_rank:,}" if isinstance(country_rank, int) and country_rank > 0 else "-"
            return f"🎹 {variant.upper()} 变体 | PP: {pp:.2f} | 全球: {gr} | 地区: {cr}"

        return f"⚠️ 未获取到 {variant.upper()} 变体排名数据"

    async def _parse_info_state(self, platform_user_id: str, raw_args: str) -> dict:
        """按参考 split_msg 行为解析 /info 参数。"""
        assert self.api_client is not None
        user_data = await self.db.get_user(platform_user_id)

        state = {
            "user": user_data["osu_id"] if user_data else 0,
            "mode": str(user_data["osu_mode"]) if user_data else "0",
            "username": user_data["osu_name"] if user_data else "",
            "day": 0,
            "source": "osu",
        }

        arg = raw_args.strip().replace("＝", "=").replace("：", ":").replace("＆", "&").replace("＃", "#")
        pattern = r"[:：]\s*(\w+)|[#＃]\s*(\d+)|[＆&]\s*(\w+)"

        for match in re.findall(pattern, arg):
            if match[0]:
                state["mode"] = match[0]
            if match[1]:
                state["day"] = int(match[1])
            if match[2]:
                source = {"sb": "ppysb", "ppysb": "ppysb"}
                state["source"] = source.get(match[2], "osu")

        arg = re.sub(pattern, "", arg).strip()
        if arg:
            state["username"] = arg
            try:
                state["user"] = await self.api_client.get_uid_by_name(arg, state["source"])
            except NetworkError:
                state["error"] = f"在 {state['source']} 服务器没有找到用户: {arg}"
                return state

        if state["source"] == "ppysb":
            if not state["mode"].isdigit() or not (0 <= int(state["mode"]) <= 6 or int(state["mode"]) == 8):
                state["error"] = "模式应为0-8(没有7)！\n0: std\n1: taiko\n2: ctb\n3: mania\n4-6: SB服 RX 模式\n8: SB服 AP 模式"
                return state
        else:
            if not state["mode"].isdigit() or not (0 <= int(state["mode"]) <= 3):
                state["error"] = "模式应为0-3！\n0: std\n1: taiko\n2: ctb\n3: mania"
                return state

        if state["day"] < 0:
            state["error"] = "查询的日期应是一个正数"
            return state

        if state["source"] == "ppysb" and not arg:
            sb_user_data = await self.db.get_sb_user(platform_user_id)
            if sb_user_data:
                state["user"] = sb_user_data["osu_id"]
                state["username"] = sb_user_data["osu_name"]
                state.pop("error", None)
            else:
                state["error"] = "该账号尚未绑定 sb 服务器，请输入 /sbbind 用户名 绑定账号"
                return state

        if state["user"] == 0:
            state["error"] = "该账号尚未绑定，请输入 /bind 用户名 绑定账号"

        return state
