import os
import sqlite3
import json
from datetime import datetime, timezone
from app.core.logger import logger

try:
    import psycopg2
except ImportError:
    psycopg2 = None

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_url = os.getenv("DATABASE_URL")
        if self.db_url:
            # Handle Render/Heroku legacy postgres:// prefix
            if self.db_url.startswith("postgres://"):
                self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
            self.is_postgres = True
            logger.info("DatabaseManager: Initializing PostgreSQL database connection.")
        else:
            self.is_postgres = False
            if db_path is None:
                # Default to course-ai/data/course_ai.db
                current_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "data"))
                os.makedirs(data_dir, exist_ok=True)
                self.db_path = os.path.join(data_dir, "course_ai.db")
            else:
                self.db_path = db_path
            logger.info(f"DatabaseManager: Initializing sqlite database at {self.db_path}")
            
        self._init_db()

    def _exec(self, sqlite_sql: str, pg_sql: str, params: tuple = ()):
        if self.is_postgres:
            if not psycopg2:
                raise ImportError("psycopg2 is required for PostgreSQL. Run: pip install psycopg2-binary")
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(pg_sql, params)
                conn.commit()
        else:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, params)
                conn.commit()

    def _fetch_one(self, sqlite_sql: str, pg_sql: str, params: tuple = ()):
        if self.is_postgres:
            if not psycopg2:
                raise ImportError("psycopg2 is required for PostgreSQL. Run: pip install psycopg2-binary")
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(pg_sql, params)
                    return cursor.fetchone()
        else:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, params)
                return cursor.fetchone()

    def _fetch_all(self, sqlite_sql: str, pg_sql: str, params: tuple = ()):
        if self.is_postgres:
            if not psycopg2:
                raise ImportError("psycopg2 is required for PostgreSQL. Run: pip install psycopg2-binary")
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(pg_sql, params)
                    return cursor.fetchall()
        else:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, params)
                return cursor.fetchall()

    def _init_db(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS roadmaps (
                topic TEXT PRIMARY KEY,
                roadmap_json TEXT,
                created_at TEXT
            );""",
            """CREATE TABLE IF NOT EXISTS lessons (
                topic TEXT PRIMARY KEY,
                lesson_json TEXT,
                created_at TEXT
            );""",
            """CREATE TABLE IF NOT EXISTS sources (
                url TEXT PRIMARY KEY,
                markdown_content TEXT,
                scraped_at TEXT
            );""",
            """CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );"""
        ]
        for sql in tables:
            self._exec(sql, sql)
        logger.info(f"DatabaseManager: Tables initialized successfully ({'PostgreSQL' if self.is_postgres else 'SQLite'}).")

    # Roadmap operations
    def save_roadmap(self, course_id: str, roadmap: dict):
        logger.info(f"Database: Saving roadmap for course '{course_id}'")
        try:
            sqlite_sql = "INSERT OR REPLACE INTO roadmaps (topic, roadmap_json, created_at) VALUES (?, ?, ?)"
            pg_sql = "INSERT INTO roadmaps (topic, roadmap_json, created_at) VALUES (%s, %s, %s) ON CONFLICT (topic) DO UPDATE SET roadmap_json = EXCLUDED.roadmap_json, created_at = EXCLUDED.created_at"
            params = (course_id.lower(), json.dumps(roadmap), datetime.now(timezone.utc).isoformat())
            self._exec(sqlite_sql, pg_sql, params)
        except Exception as e:
            logger.error(f"Database error saving roadmap: {e}")

    def get_roadmap(self, course_id: str) -> dict:
        logger.info(f"Database: Fetching roadmap for course '{course_id}'")
        try:
            sqlite_sql = "SELECT roadmap_json FROM roadmaps WHERE topic = ?"
            pg_sql = "SELECT roadmap_json FROM roadmaps WHERE topic = %s"
            row = self._fetch_one(sqlite_sql, pg_sql, (course_id.lower(),))
            if row:
                data = json.loads(row[0])
                if isinstance(data, dict):
                    if "title" in data and "course" not in data:
                        data["course"] = data["title"]
                    if "id" not in data:
                        data["id"] = course_id.lower()
                return data
        except Exception as e:
            logger.error(f"Database error fetching roadmap: {e}")
        return None

    # Lesson operations
    def save_lesson(self, course_id: str, chapter_id: int, lesson: dict):
        key = f"{course_id.lower()}_{chapter_id}"
        logger.info(f"Database: Saving lesson for key '{key}'")
        try:
            sqlite_sql = "INSERT OR REPLACE INTO lessons (topic, lesson_json, created_at) VALUES (?, ?, ?)"
            pg_sql = "INSERT INTO lessons (topic, lesson_json, created_at) VALUES (%s, %s, %s) ON CONFLICT (topic) DO UPDATE SET lesson_json = EXCLUDED.lesson_json, created_at = EXCLUDED.created_at"
            params = (key, json.dumps(lesson), datetime.now(timezone.utc).isoformat())
            self._exec(sqlite_sql, pg_sql, params)
        except Exception as e:
            logger.error(f"Database error saving lesson: {e}")

    def get_lesson(self, course_id: str, chapter_id: int) -> dict:
        key = f"{course_id.lower()}_{chapter_id}"
        logger.info(f"Database: Fetching lesson for key '{key}'")
        try:
            sqlite_sql = "SELECT lesson_json FROM lessons WHERE topic = ?"
            pg_sql = "SELECT lesson_json FROM lessons WHERE topic = %s"
            row = self._fetch_one(sqlite_sql, pg_sql, (key,))
            if row:
                return json.loads(row[0])
        except Exception as e:
            logger.error(f"Database error fetching lesson: {e}")
        return None

    # Sources operations
    def save_source(self, url: str, content: str):
        logger.info(f"Database: Saving scraped source from URL: '{url}'")
        try:
            sqlite_sql = "INSERT OR REPLACE INTO sources (url, markdown_content, scraped_at) VALUES (?, ?, ?)"
            pg_sql = "INSERT INTO sources (url, markdown_content, scraped_at) VALUES (%s, %s, %s) ON CONFLICT (url) DO UPDATE SET markdown_content = EXCLUDED.markdown_content, scraped_at = EXCLUDED.scraped_at"
            params = (url, content, datetime.now(timezone.utc).isoformat())
            self._exec(sqlite_sql, pg_sql, params)
        except Exception as e:
            logger.error(f"Database error saving source: {e}")

    def get_source(self, url: str) -> str:
        logger.info(f"Database: Fetching source for URL: '{url}'")
        try:
            sqlite_sql = "SELECT markdown_content FROM sources WHERE url = ?"
            pg_sql = "SELECT markdown_content FROM sources WHERE url = %s"
            row = self._fetch_one(sqlite_sql, pg_sql, (url,))
            if row:
                return row[0]
        except Exception as e:
            logger.error(f"Database error fetching source: {e}")
        return None

    # Metadata operations
    def save_metadata(self, key: str, value: str):
        try:
            sqlite_sql = "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)"
            pg_sql = "INSERT INTO metadata (key, value, updated_at) VALUES (%s, %s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at"
            params = (key, value, datetime.now(timezone.utc).isoformat())
            self._exec(sqlite_sql, pg_sql, params)
        except Exception as e:
            logger.error(f"Database error saving metadata: {e}")

    def get_metadata(self, key: str) -> str:
        try:
            sqlite_sql = "SELECT value FROM metadata WHERE key = ?"
            pg_sql = "SELECT value FROM metadata WHERE key = %s"
            row = self._fetch_one(sqlite_sql, pg_sql, (key,))
            if row:
                return row[0]
        except Exception as e:
            logger.error(f"Database error fetching metadata: {e}")
        return None

    def get_all_roadmaps(self) -> list:
        try:
            sql = "SELECT topic, roadmap_json FROM roadmaps"
            rows = self._fetch_all(sql, sql)
            result = []
            for r in rows:
                topic_id = r[0]
                data = json.loads(r[1])
                if isinstance(data, dict):
                    if "title" in data and "course" not in data:
                        data["course"] = data["title"]
                    if "id" not in data:
                        data["id"] = topic_id.lower()
                result.append({"topic": topic_id, "roadmap": data})
            return result
        except Exception as e:
            logger.error(f"Database error fetching all roadmaps: {e}")
        return []

db = DatabaseManager()
