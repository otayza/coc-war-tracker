import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "wars.db")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS war_participation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_tag TEXT NOT NULL DEFAULT '',
                player_tag TEXT NOT NULL,
                player_name TEXT NOT NULL,
                townhall_level INTEGER DEFAULT 0,
                stars INTEGER DEFAULT 0,
                attacks INTEGER DEFAULT 0,
                war_end_time TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migraciones
        columns = [row[1] for row in self.conn.execute("PRAGMA table_info(war_participation)").fetchall()]
        if "clan_tag" not in columns:
            self.conn.execute("ALTER TABLE war_participation ADD COLUMN clan_tag TEXT NOT NULL DEFAULT ''")
        if "townhall_level" not in columns:
            self.conn.execute("ALTER TABLE war_participation ADD COLUMN townhall_level INTEGER DEFAULT 0")
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_tag ON war_participation(player_tag)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_war_end_time ON war_participation(war_end_time)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clan_tag ON war_participation(clan_tag)
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS war_state (
                clan_tag TEXT NOT NULL,
                war_end_time TEXT NOT NULL,
                total_attacks INTEGER DEFAULT 0,
                PRIMARY KEY (clan_tag, war_end_time)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS clan_members (
                clan_tag TEXT NOT NULL,
                player_tag TEXT NOT NULL,
                player_name TEXT NOT NULL,
                townhall_level INTEGER DEFAULT 0,
                PRIMARY KEY (clan_tag, player_tag)
            )
        """)
        self.conn.commit()

    def sync_clan_members(self, clan_tag: str, members: list) -> bool:
        """Actualiza la lista de miembros del clan. Devuelve True si hubo cambios."""
        existing = {
            (row["player_tag"], row["player_name"], row["townhall_level"])
            for row in self.conn.execute(
                "SELECT player_tag, player_name, townhall_level FROM clan_members WHERE clan_tag = ?", (clan_tag,)
            ).fetchall()
        }
        new = {
            (m.get("tag"), m.get("name"), m.get("townHallLevel", 0))
            for m in members
        }

        if existing == new:
            return False

        self.conn.execute("DELETE FROM clan_members WHERE clan_tag = ?", (clan_tag,))
        for m in members:
            self.conn.execute(
                """INSERT INTO clan_members (clan_tag, player_tag, player_name, townhall_level)
                   VALUES (?, ?, ?, ?)""",
                (clan_tag, m.get("tag"), m.get("name"), m.get("townHallLevel", 0))
            )
        self.conn.commit()
        return True

    def get_war_attack_count(self, clan_tag: str, war_end_time: str) -> int:
        """Obtiene el número de ataques registrados en la última ejecución."""
        row = self.conn.execute(
            "SELECT total_attacks FROM war_state WHERE clan_tag = ? AND war_end_time = ?",
            (clan_tag, war_end_time)
        ).fetchone()
        return row["total_attacks"] if row else -1

    def update_war_attack_count(self, clan_tag: str, war_end_time: str, total_attacks: int):
        """Actualiza el número de ataques de la guerra actual."""
        self.conn.execute(
            """INSERT INTO war_state (clan_tag, war_end_time, total_attacks)
               VALUES (?, ?, ?)
               ON CONFLICT(clan_tag, war_end_time) DO UPDATE SET total_attacks = ?""",
            (clan_tag, war_end_time, total_attacks, total_attacks)
        )
        self.conn.commit()

    def upsert_participation(self, clan_tag: str, player_tag: str, player_name: str, townhall_level: int, stars: int, attacks: int, war_end_time: str):
        existing = self.conn.execute(
            "SELECT id FROM war_participation WHERE clan_tag = ? AND player_tag = ? AND war_end_time = ?",
            (clan_tag, player_tag, war_end_time)
        ).fetchone()
        if existing:
            self.conn.execute(
                """UPDATE war_participation SET player_name = ?, townhall_level = ?, stars = ?, attacks = ?
                   WHERE clan_tag = ? AND player_tag = ? AND war_end_time = ?""",
                (player_name, townhall_level, stars, attacks, clan_tag, player_tag, war_end_time)
            )
        else:
            self.conn.execute(
                """INSERT INTO war_participation (clan_tag, player_tag, player_name, townhall_level, stars, attacks, war_end_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (clan_tag, player_tag, player_name, townhall_level, stars, attacks, war_end_time)
            )
        self.conn.commit()

    def get_player_stats(self, clan_tag: str):
        rows = self.conn.execute("""
            SELECT
                cm.player_name,
                cm.player_tag,
                cm.townhall_level,
                COALESCE(wp.wars_played, 0) as wars_played,
                COALESCE(wp.total_stars, 0) as total_stars,
                COALESCE(wp.total_attacks, 0) as total_attacks,
                COALESCE(wp.avg_stars, 0) as avg_stars
            FROM clan_members cm
            LEFT JOIN (
                SELECT
                    player_tag,
                    MAX(townhall_level) as th,
                    COUNT(*) as wars_played,
                    SUM(stars) as total_stars,
                    SUM(attacks) as total_attacks,
                    ROUND(CASE WHEN SUM(attacks) > 0 THEN SUM(stars) * 1.0 / SUM(attacks) ELSE 0 END, 2) as avg_stars
                FROM war_participation
                WHERE clan_tag = ?
                GROUP BY player_tag
            ) wp ON cm.player_tag = wp.player_tag
            WHERE cm.clan_tag = ?
            ORDER BY total_stars DESC, cm.townhall_level DESC
        """, (clan_tag, clan_tag)).fetchall()
        return [dict(row) for row in rows]

    def get_recent_wars(self, clan_tag: str, limit=10):
        rows = self.conn.execute("""
            SELECT DISTINCT war_end_time
            FROM war_participation
            WHERE clan_tag = ?
            ORDER BY war_end_time DESC
            LIMIT ?
        """, (clan_tag, limit)).fetchall()
        return [row["war_end_time"] for row in rows]

    def purge_old_records(self, max_wars=30):
        """Elimina registros de guerras antiguas, manteniendo solo las últimas max_wars por clan."""
        # Obtener guerras a mantener por clan
        clans = self.conn.execute("SELECT DISTINCT clan_tag FROM war_participation").fetchall()
        for clan_row in clans:
            ct = clan_row["clan_tag"]
            wars_to_keep = self.conn.execute("""
                SELECT DISTINCT war_end_time FROM war_participation
                WHERE clan_tag = ?
                ORDER BY war_end_time DESC
                LIMIT ?
            """, (ct, max_wars)).fetchall()
            keep_times = [r["war_end_time"] for r in wars_to_keep]
            if keep_times:
                placeholders = ",".join("?" * len(keep_times))
                self.conn.execute(f"""
                    DELETE FROM war_participation
                    WHERE clan_tag = ? AND war_end_time NOT IN ({placeholders})
                """, [ct] + keep_times)
        self.conn.execute("""
            DELETE FROM war_state
            WHERE (clan_tag, war_end_time) NOT IN (
                SELECT DISTINCT clan_tag, war_end_time
                FROM war_participation
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()
