"""数据库模型定义"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, date


class Database:
    """简单的 SQLite 数据库管理器"""

    def __init__(self, db_path: str = "./osuscore.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 用户绑定表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                osu_id INTEGER NOT NULL,
                osu_name TEXT NOT NULL,
                osu_mode INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 成绩缓存表（最近查询的成绩）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osu_id INTEGER NOT NULL,
                beatmap_id INTEGER NOT NULL,
                score_id INTEGER NOT NULL,
                score_data TEXT NOT NULL,
                query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    async def get_user(self, user_id: str):
        """获取用户绑定信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM user_data WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(result)
        return None

    async def save_user(self, user_id: str, osu_id: int, osu_name: str, osu_mode: int = 0):
        """保存/更新用户绑定信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO user_data (user_id, osu_id, osu_name, osu_mode)
            VALUES (?, ?, ?, ?)
        """, (user_id, osu_id, osu_name, osu_mode))

        conn.commit()
        conn.close()

    async def get_recent_score(self, osu_id: int):
        """获取缓存的最近成绩"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM recent_scores
            WHERE osu_id = ?
            ORDER BY query_time DESC
            LIMIT 1
        """, (osu_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "osu_id": result["osu_id"],
                "beatmap_id": result["beatmap_id"],
                "score_id": result["score_id"],
                "score_data": json.loads(result["score_data"]),
                "query_time": result["query_time"]
            }
        return None

    async def save_recent_score(self, osu_id: int, beatmap_id: int, score_id: int, score_data: dict):
        """缓存最近成绩"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO recent_scores (osu_id, beatmap_id, score_id, score_data)
            VALUES (?, ?, ?, ?)
        """, (osu_id, beatmap_id, score_id, json.dumps(score_data, default=str)))

        conn.commit()
        conn.close()
