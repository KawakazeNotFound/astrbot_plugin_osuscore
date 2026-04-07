"""OSU API 接口"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel


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

    async def get_user(self, user_identifier: str) -> Dict[str, Any]:
        """
        获取用户信息
        user_identifier: 用户 ID 或用户名
        """
        headers = await self._get_headers()
        url = f"{self.api_base}/users/{user_identifier}/osu"

        response = await self.client.get(url, headers=headers)
        if response.status_code == 404:
            raise Exception(f"User not found: {user_identifier}")
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        return response.json()

    async def get_user_scores(
        self,
        user_id: int,
        mode: str = "osu",
        scope: str = "recent",
        limit: int = 1,
        offset: int = 0,
        legacy_only: bool = False
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
            "legacy_only": legacy_only
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
