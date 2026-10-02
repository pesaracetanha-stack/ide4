# -*- coding: utf-8 -*-
# codesaver/core/version_history.py
import os
import sqlite3
import logging
from datetime import datetime

class VersionHistoryManager:
    # 🚀 LIMITER: نگهداری حداکثر ۵۰ نسخه‌ی آخر برای جلوگیری از انفجار حجم دیتابیس
    MAX_VERSIONS = 50 

    def __init__(self):
        self.project_root = ""
        self.db_path = ""

    def set_project_root(self, project_root: str):
        self.project_root = project_root
        if project_root:
            codesaver_dir = os.path.join(project_root, ".codesaver")
            self.db_path = os.path.join(codesaver_dir, "history.db")
            try:
                os.makedirs(codesaver_dir, exist_ok=True)
                self._init_db()
            except Exception as e:
                logging.error(f"Error initializing DB directory: {e}")

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        content TEXT NOT NULL
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON versions(file_path)')
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error creating tables: {e}")

    def _get_safe_path(self, file_path: str) -> str:
        try:
            if self.project_root:
                return os.path.relpath(file_path, self.project_root)
        except ValueError:
            pass
        return os.path.abspath(file_path)

    def save_version(self, file_path: str, content: str) -> bool:
        if not self.db_path:
            return False

        try:
            safe_path = self._get_safe_path(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO versions (file_path, timestamp, content)
                    VALUES (?, ?, ?)
                ''', (safe_path, timestamp, content))
                
                # 🚀 FIX: اضافه کردن id DESC تا در صورت ثبت چند سیو در یک ثانیه، فقط جدیدترین‌ها نگه داشته شوند
                cursor.execute('''
                    DELETE FROM versions 
                    WHERE id NOT IN (
                        SELECT id FROM versions 
                        WHERE file_path = ? 
                        ORDER BY timestamp DESC, id DESC 
                        LIMIT ?
                    ) AND file_path = ?
                ''', (safe_path, self.MAX_VERSIONS, safe_path))
                
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error saving history log: {e}")
            return False

    def get_versions(self, file_path: str) -> list:
        versions = []
        if not self.db_path or not file_path or not os.path.exists(self.db_path):
            return versions

        try:
            safe_path = self._get_safe_path(file_path)
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                # 🚀 FIX: مرتب‌سازی با id DESC برای اطمینان از تقدم نسخه‌های جدیدتر در یک ثانیه
                cursor.execute('''
                    SELECT timestamp FROM versions 
                    WHERE file_path = ? 
                    ORDER BY timestamp DESC, id DESC
                ''', (safe_path,))
                
                seen = set()
                for row in cursor.fetchall():
                    time_str = row[0]
                    # جلوگیری از نمایش زمان‌های تکراری در لیست تاریخچه (رابط کاربری)
                    if time_str not in seen:  
                        try:
                            versions.append(datetime.strptime(time_str, "%Y%m%d_%H%M%S"))
                            seen.add(time_str)
                        except ValueError:
                            pass
        except Exception as e:
            logging.error(f"Error fetching timestamps: {e}")
        
        return versions

    def load_version(self, file_path: str, timestamp: datetime):
        if not self.db_path or not file_path or not timestamp:
            return None

        try:
            safe_path = self._get_safe_path(file_path)
            time_str = timestamp.strftime("%Y%m%d_%H%M%S")

            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                # 🚀 FIX: گرفتن آخرین نسخه با id DESC در صورتی که کاربر در یک ثانیه چند بار سیو کرده باشد
                cursor.execute('''
                    SELECT content FROM versions 
                    WHERE file_path = ? AND timestamp = ?
                    ORDER BY id DESC
                    LIMIT 1
                ''', (safe_path, time_str))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logging.error(f"Error reading version: {e}")
            return None