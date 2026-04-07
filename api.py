"""OSU API 接口"""

import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel

from .exceptions import NetworkError
from .info_models import UnifiedUser, GradeCounts, Level, UserStatistics


class TokenCache:
    """Token 缓存管理器"""

    def __init__(self, max_age_seconds: int = 86400):
        self.token: Optional[str] = None
        self.token_time: Optional[datetime] = None
        self.max_age_seconds = max_age_seconds
        self._lock = asyncio.Lock()

    async def get_token(self) -> Optional[str]:
        """获取有效的 token"""
        if self.token and self.token_time:
            age = (datetime.now() - self.token_time).total_seconds()
            if age < self.max_age_seconds:
                return self.token
        return None

    async def set_token(self, token: str):
        """设置 token"""
        async with self._lock:
            self.token = token
            self.token_time = datetime.now()


class OsuApiClient:
    """OSU API 客户端"""

    def __init__(self, client_id: int, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_base = "https://osu.ppy.sh/api/v2"
        self.token_cache = TokenCache()
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _request_json(self, url: str, headers: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        response = await self.client.get(url, headers=headers, params=params)
        if response.status_code == 404:
            raise NetworkError("未找到该玩家，请确认玩家ID")
        if response.status_code != 200:
            raise NetworkError(f"API 请求失败: HTTP {response.status_code}")
        return response.json()

    async def _request_public_json(self, url: str, not_found_message: str) -> dict:
        response = await self.client.get(url)
        if response.status_code == 404:
            raise NetworkError(not_found_message)
        if response.status_code != 200:
            raise NetworkError(f"API 请求失败: HTTP {response.status_code}")
        return response.json()

    async def _get_token(self) -> str:
        """获取或刷新 access token"""
        cached_token = await self.token_cache.get_token()
        if cached_token:
            return cached_token

        # 请求新 token
        token_url = "https://osu.ppy.sh/oauth/token"
        response = await self.client.post(
            token_url,
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "public",
            }
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.text}")

        data = response.json()
        token = data["access_token"]
        await self.token_cache.set_token(token)
        return token

    async def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "x-api-version": "20220705"
        }

    async def get_user(self, user_identifier: str, mode: str = "osu") -> Dict[str, Any]:
        """
        获取用户信息
        user_identifier: 用户 ID 或用户名
        """
        headers = await self._get_headers()
        url = f"{self.api_base}/users/{user_identifier}/{mode}"
        return await self._request_json(url, headers=headers)

    async def get_user_scores(
        self,
        user_id: int,
        mode: str = "osu",
        scope: str = "recent",
        limit: int = 1,
        offset: int = 0,
        legacy_only: bool = False,
        include_failed: bool = False,
    ) -> list:
        """
        获取用户成绩
        scope: 'best' 或 'recent'
        """
        headers = await self._get_headers()
        url = f"{self.api_base}/users/{user_id}/scores/{scope}"

        params = {
            "mode": mode,
            "limit": limit,
            "offset": offset,
            "legacy_only": legacy_only,
            "include_fails": int(include_failed),
        }

        response = await self.client.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        return response.json()

    async def get_beatmap(self, beatmap_id: int) -> Dict[str, Any]:
        """获取谱面信息"""
        headers = await self._get_headers()
        url = f"{self.api_base}/beatmaps/{beatmap_id}"

        response = await self.client.get(url, headers=headers)
        if response.status_code == 404:
            raise Exception(f"Beatmap not found: {beatmap_id}")
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        return response.json()

    async def get_uid_by_name(self, name: str, source: str = "osu") -> int:
        if source == "osu":
            headers = await self._get_headers()
            data = await self._request_json(f"{self.api_base}/users/@{name}", headers=headers)
            return data["id"]

        if source == "ppysb":
            data = await self._request_public_json(
                f"https://api.ppy.sb/v1/get_player_info?scope=all&name={name}",
                "未找到该玩家，请确认玩家ID是否正确",
            )
            return int(data["player"]["info"]["id"])

        raise NetworkError(f"不支持的服务器: {source}")

    async def get_user_info_data(self, uid: Union[int, str], mode: str, source: str = "osu") -> UnifiedUser:
        if source == "osu":
            if mode not in {"osu", "taiko", "fruits", "mania"}:
                raise NetworkError("模式应为0-3！\n0: std\n1: taiko\n2: ctb\n3: mania")

            headers = await self._get_headers()
            data = await self._request_json(f"{self.api_base}/users/{uid}/{mode}", headers=headers)
            if not data.get("cover_url"):
                cover = data.get("cover")
                if isinstance(cover, dict):
                    data["cover_url"] = cover.get("custom_url") or cover.get("url")
            return UnifiedUser(**data)

        if source == "ppysb":
            data = await self._request_public_json(
                f"https://api.ppy.sb/v1/get_player_info?scope=all&id={uid}",
                "未找到该玩家，请确认玩家ID",
            )
            player = data.get("player", {})
            info_data = player.get("info", {})
            stats = player.get("stats", {})

            mode_map = {
                "osu": "0",
                "taiko": "1",
                "fruits": "2",
                "mania": "3",
                "rxosu": "4",
                "rxtaiko": "5",
                "rxfruits": "6",
                "aposu": "8",
            }
            mode_key = mode_map.get(mode)
            if mode_key is None:
                raise NetworkError("模式应为0-8(没有7)！\n0: std\n1: taiko\n2: ctb\n3: mania\n4-6: SB服 RX 模式\n8: SB服 AP 模式")

            mode_stats = stats.get(mode_key, {})

            def _to_int(v, default=0):
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return default

            def _to_float(v, default=0.0):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return default

            user_statistics = UserStatistics(
                grade_counts=GradeCounts(
                    ssh=_to_int(mode_stats.get("xh_count")),
                    ss=_to_int(mode_stats.get("x_count")),
                    sh=_to_int(mode_stats.get("sh_count")),
                    s=_to_int(mode_stats.get("s_count")),
                    a=_to_int(mode_stats.get("a_count")),
                ),
                hit_accuracy=_to_float(mode_stats.get("acc")),
                level=Level(current=100, progress=99),
                maximum_combo=_to_int(mode_stats.get("max_combo")),
                play_count=_to_int(mode_stats.get("plays")),
                play_time=_to_int(mode_stats.get("playtime")),
                pp=_to_float(mode_stats.get("pp")),
                ranked_score=_to_int(mode_stats.get("rscore")),
                replays_watched_by_others=0,
                total_hits=_to_int(mode_stats.get("total_hits")),
                total_score=_to_int(mode_stats.get("tscore")),
                global_rank=_to_int(mode_stats.get("rank")) or None,
                country_rank=_to_int(mode_stats.get("country_rank")) or None,
            )

            user_id = _to_int(info_data.get("id"))
            return UnifiedUser(
                avatar_url=f"https://a.ppy.sb/{user_id}",
                country_code=str(info_data.get("country", "xx")).upper(),
                id=user_id,
                username=str(info_data.get("name", uid)),
                is_supporter=False,
                statistics=user_statistics,
            )

        raise NetworkError(f"不支持的服务器: {source}")

    async def get_image_bytes(self, url: str) -> bytes:
        async def _fetch_image(target_url: str, depth: int = 0) -> bytes:
            response = await self.client.get(target_url, follow_redirects=True)
            if response.status_code != 200:
                raise NetworkError(f"背景下载失败: HTTP {response.status_code}")

            content_type = (response.headers.get("content-type") or "").lower()
            if content_type.startswith("image/"):
                return response.content

            if depth >= 1:
                raise NetworkError("背景下载失败: 返回内容不是图片")

            next_url: Optional[str] = None
            try:
                payload = response.json()
            except ValueError:
                payload = None

            if isinstance(payload, dict):
                for key in ("url", "image", "img", "pic", "background", "bg_url"):
                    value = payload.get(key)
                    if isinstance(value, str) and value.startswith("http"):
                        next_url = value
                        break
            elif isinstance(payload, list) and payload:
                first = payload[0]
                if isinstance(first, str) and first.startswith("http"):
                    next_url = first

            if next_url is None:
                text = response.text.strip()
                if text.startswith("http"):
                    next_url = text

            if next_url is None:
                raise NetworkError("背景下载失败: 返回内容不是图片")

            return await _fetch_image(next_url, depth + 1)

        return await _fetch_image(url)

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()


# 内置数据模型定义
class UserBasic(BaseModel):
    id: int
    username: str
    avatar_url: str
    country_code: str


class BeatmapInfo(BaseModel):
    id: int
    beatmapset_id: int
    version: str
    difficulty_rating: float
    cs: float
    ar: float
    od: float
    hp: float


class BeatmapSet(BaseModel):
    id: int
    title: str
    artist: str
    creator: str


class ScoreMod(BaseModel):
    acronym: str


class ScoreInfo(BaseModel):
    id: int
    user_id: int
    beatmap_id: int
    score: int
    accuracy: float
    max_combo: int
    mods: list[ScoreMod] = []
    created_at: str
    rank: str
    passed: bool = True
