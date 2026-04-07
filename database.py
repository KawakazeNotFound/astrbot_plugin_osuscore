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

        # SB 服务器用户绑定表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sb_user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                osu_id INTEGER NOT NULL,
                osu_name TEXT NOT NULL,
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

        # 用户信息快照表（用于 /info 变化量对比）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS info_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osu_id INTEGER NOT NULL,
                c_rank INTEGER,
                g_rank INTEGER,
                pp REAL NOT NULL,
                acc REAL NOT NULL,
                pc INTEGER NOT NULL,
                count INTEGER NOT NULL,
                osu_mode INTEGER NOT NULL,
                date DATE NOT NULL,
                ranked_score INTEGER,
                total_score INTEGER,
                max_combo INTEGER,
                count_xh INTEGER,
                count_x INTEGER,
                count_sh INTEGER,
                count_s INTEGER,
                count_a INTEGER,
                replays INTEGER,
                play_time INTEGER,
                badge_count INTEGER,
                UNIQUE(osu_id, osu_mode, date)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_info_data_user_mode_date ON info_data(osu_id, osu_mode, date)"
        )

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

    async def delete_user(self, user_id: str):
        """删除用户绑定信息。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_data WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    async def get_sb_user(self, user_id: str):
        """获取 SB 服务器用户绑定信息。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sb_user_data WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(result)
        return None

    async def save_sb_user(self, user_id: str, osu_id: int, osu_name: str):
        """保存/更新 SB 服务器用户绑定信息。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO sb_user_data (user_id, osu_id, osu_name)
            VALUES (?, ?, ?)
            """,
            (user_id, osu_id, osu_name),
        )
        conn.commit()
        conn.close()

    async def delete_sb_user(self, user_id: str):
        """删除 SB 服务器用户绑定信息。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sb_user_data WHERE user_id = ?", (user_id,))
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

    async def get_latest_info_data(self, osu_id: int, osu_mode: int):
        """获取用户某模式最新一条信息快照。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM info_data
            WHERE osu_id = ? AND osu_mode = ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (osu_id, osu_mode),
        )
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    async def get_info_data_since(self, osu_id: int, osu_mode: int, query_date: date):
        """获取 >= query_date 的最早一条快照。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM info_data
            WHERE osu_id = ? AND osu_mode = ? AND date >= ?
            ORDER BY date ASC
            LIMIT 1
            """,
            (osu_id, osu_mode, query_date.isoformat()),
        )
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    async def ensure_today_country_rank(self, osu_id: int, osu_mode: int, today_date: date, country_rank: int | None):
        """若今日快照 c_rank 为空，则补全。"""
        if country_rank is None:
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE info_data
            SET c_rank = ?
            WHERE osu_id = ? AND osu_mode = ? AND date = ? AND c_rank IS NULL
            """,
            (country_rank, osu_id, osu_mode, today_date.isoformat()),
        )
        conn.commit()
        conn.close()

    async def upsert_info_data(
        self,
        osu_id: int,
        osu_mode: int,
        date_value: date,
        c_rank: int | None,
        g_rank: int | None,
        pp: float,
        acc: float,
        pc: int,
        count: int,
        ranked_score: int | None,
        total_score: int | None,
        max_combo: int | None,
        count_xh: int | None,
        count_x: int | None,
        count_sh: int | None,
        count_s: int | None,
        count_a: int | None,
        replays: int | None,
        play_time: int | None,
        badge_count: int | None,
    ):
        """按 (osu_id, osu_mode, date) UPSERT 信息快照。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO info_data (
                osu_id, c_rank, g_rank, pp, acc, pc, count, osu_mode, date,
                ranked_score, total_score, max_combo,
                count_xh, count_x, count_sh, count_s, count_a,
                replays, play_time, badge_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(osu_id, osu_mode, date) DO UPDATE SET
                c_rank = excluded.c_rank,
                g_rank = excluded.g_rank,
                pp = excluded.pp,
                acc = excluded.acc,
                pc = excluded.pc,
                count = excluded.count,
                ranked_score = excluded.ranked_score,
                total_score = excluded.total_score,
                max_combo = excluded.max_combo,
                count_xh = excluded.count_xh,
                count_x = excluded.count_x,
                count_sh = excluded.count_sh,
                count_s = excluded.count_s,
                count_a = excluded.count_a,
                replays = excluded.replays,
                play_time = excluded.play_time,
                badge_count = excluded.badge_count
            """,
            (
                osu_id,
                c_rank,
                g_rank,
                pp,
                acc,
                pc,
                count,
                osu_mode,
                date_value.isoformat(),
                ranked_score,
                total_score,
                max_combo,
                count_xh,
                count_x,
                count_sh,
                count_s,
                count_a,
                replays,
                play_time,
                badge_count,
            ),
        )
        conn.commit()
        conn.close()
