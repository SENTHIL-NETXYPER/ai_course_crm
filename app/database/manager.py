import os
import sqlite3
import json
from datetime import datetime
from app.core.logger import logger

class DatabaseManager:
    def __init__(self, db_path: str = None):
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

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Roadmaps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roadmaps (
                    topic TEXT PRIMARY KEY,
                    roadmap_json TEXT,
                    created_at TEXT
                )
            """)
            
            # 2. Lessons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    topic TEXT PRIMARY KEY,
                    lesson_json TEXT,
                    created_at TEXT
                )
            """)
            
            # 3. Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    url TEXT PRIMARY KEY,
                    markdown_content TEXT,
                    scraped_at TEXT
                )
            """)
            
            # 4. Metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()
            logger.info("DatabaseManager: Tables initialized successfully.")

    # Roadmap operations
    def save_roadmap(self, course_id: str, roadmap: dict):
        logger.info(f"Database: Saving roadmap for course '{course_id}'")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO roadmaps (topic, roadmap_json, created_at) VALUES (?, ?, ?)",
                    (course_id.lower(), json.dumps(roadmap), datetime.utcnow().isoformat())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Database error saving roadmap: {e}")

    def get_roadmap(self, course_id: str) -> dict:
        logger.info(f"Database: Fetching roadmap for course '{course_id}'")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT roadmap_json FROM roadmaps WHERE topic = ?", (course_id.lower(),))
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    # Dynamic schema migration/fallback for roadmaps
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO lessons (topic, lesson_json, created_at) VALUES (?, ?, ?)",
                    (key, json.dumps(lesson), datetime.utcnow().isoformat())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Database error saving lesson: {e}")

    def get_lesson(self, course_id: str, chapter_id: int) -> dict:
        key = f"{course_id.lower()}_{chapter_id}"
        logger.info(f"Database: Fetching lesson for key '{key}'")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT lesson_json FROM lessons WHERE topic = ?", (key,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            logger.error(f"Database error fetching lesson: {e}")
        return None

    # Sources operations
    def save_source(self, url: str, content: str):
        logger.info(f"Database: Saving scraped source from URL: '{url}'")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO sources (url, markdown_content, scraped_at) VALUES (?, ?, ?)",
                    (url, content, datetime.utcnow().isoformat())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Database error saving source: {e}")

    def get_source(self, url: str) -> str:
        logger.info(f"Database: Fetching source for URL: '{url}'")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT markdown_content FROM sources WHERE url = ?", (url,))
                row = cursor.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            logger.error(f"Database error fetching source: {e}")
        return None

    # Metadata operations
    def save_metadata(self, key: str, value: str):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, value, datetime.utcnow().isoformat())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Database error saving metadata: {e}")

    def get_metadata(self, key: str) -> str:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            logger.error(f"Database error fetching metadata: {e}")
        return None

    def get_all_roadmaps(self) -> list:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT topic, roadmap_json FROM roadmaps")
                rows = cursor.fetchall()
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
