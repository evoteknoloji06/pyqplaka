import sqlite3
import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='data/lpr_system.db'):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plates (
                    plate TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate TEXT,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    image_path TEXT
                )
            ''')
            conn.commit()

    def add_plate(self, plate, status):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO plates (plate, status) VALUES (?, ?)', (plate.upper(), status))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding plate: {e}")
            return False

    def delete_plate(self, plate):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM plates WHERE plate = ?', (plate.upper(),))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting plate: {e}")
            return False

    def get_plate_status(self, plate):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT status FROM plates WHERE plate = ?', (plate.upper(),))
                result = cursor.fetchone()
                return result[0] if result else 'Guest'
        except Exception as e:
            print(f"Error getting plate status: {e}")
            return 'Guest'

    def get_all_plates(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT plate, status FROM plates')
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting all plates: {e}")
            return []

    def log_detection(self, plate, status, image_path=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO logs (plate, status, image_path) VALUES (?, ?, ?)', 
                               (plate.upper(), status, image_path))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging detection: {e}")
            return False

    def get_recent_logs(self, limit=50):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT plate, status, timestamp, image_path FROM logs ORDER BY timestamp DESC LIMIT ?', (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
