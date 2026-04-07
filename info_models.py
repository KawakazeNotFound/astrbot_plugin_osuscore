from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class CompatBaseModel(BaseModel):
    class Config:
        extra = "ignore"

    def model_dump(self, **kwargs) -> dict[str, Any]:
        if hasattr(BaseModel, "model_dump"):
            return BaseModel.model_dump(self, **kwargs)  # type: ignore[attr-defined]
        return self.dict(**kwargs)

    def model_dump_json(self, **kwargs) -> str:
        if hasattr(BaseModel, "model_dump_json"):
            return BaseModel.model_dump_json(self, **kwargs)  # type: ignore[attr-defined]
        return self.json(**kwargs)


class Badge(CompatBaseModel):
    awarded_at: str
    description: str
    image_url: str
    url: str


class GradeCounts(CompatBaseModel):
    ssh: int
    ss: int
    sh: int
    s: int
    a: int


class Level(CompatBaseModel):
    current: int
    progress: int


class Variant(CompatBaseModel):
    mode: str
    variant: str
    country_rank: Optional[int] = None
    global_rank: Optional[int] = None
    pp: Optional[float] = None


class UserStatistics(CompatBaseModel):
    grade_counts: GradeCounts
    hit_accuracy: float
    is_ranked: bool = True
    level: Level
    maximum_combo: int
    play_count: int
    play_time: int
    pp: float
    ranked_score: int
    replays_watched_by_others: int
    total_hits: int
    total_score: int
    global_rank: Optional[int] = None
    country_rank: Optional[int] = None
    badges: Optional[list[Badge]] = None
    variants: Optional[list[Variant]] = None
    global_rank_percent: Optional[float] = None


class Team(CompatBaseModel):
    flag_url: Optional[str] = None
    id: Optional[int] = None
    name: str
    short_name: Optional[str] = None


class UnifiedUser(CompatBaseModel):
    avatar_url: str
    cover_url: Optional[str] = None
    country_code: str
    id: int
    username: str
    is_supporter: bool = False
    badges: Optional[list[Badge]] = None
    statistics: Optional[UserStatistics] = None
    team: Optional[Team] = None


class DrawStatistics(CompatBaseModel):
    level: Level
    global_rank: Optional[int] = None
    global_rank_percent: Optional[float] = None
    country_rank: Optional[int] = None
    pp: float
    grade_counts: GradeCounts
    ranked_score: int
    hit_accuracy: float
    play_count: int
    total_score: int
    total_hits: int
    play_time: int
    maximum_combo: int
    replays_watched_by_others: int
    variants: Optional[list[Variant]] = None


class DrawUser(CompatBaseModel):
    id: int
    username: str
    country_code: str
    team: Optional[Team] = None
    footer: str
    mode: str
    badges: Optional[list[Badge]] = None
    statistics: Optional[DrawStatistics] = None
    rank_change: Optional[str] = None
    country_rank_change: Optional[str] = None
    pp_change: Optional[str] = None
    acc_change: Optional[str] = None
    pc_change: Optional[str] = None
    hits_change: Optional[str] = None
    ranked_score_change: Optional[str] = None
    total_score_change: Optional[str] = None
    xh_change: Optional[str] = None
    x_change: Optional[str] = None
    sh_change: Optional[str] = None
    s_change: Optional[str] = None
    a_change: Optional[str] = None
    play_time_change: Optional[str] = None
    badge_count_change: Optional[str] = None
