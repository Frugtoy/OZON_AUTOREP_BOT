import sqlite3
from typing import List, Dict, Any, Optional
from config import settings


class ReviewManager:
    def __init__(self, db_name: Optional[str] = None):
        self.db_name = db_name or settings.db_path
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self) -> None:
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                sku INTEGER,
                text TEXT,
                published_at TEXT,
                rating INTEGER,
                status TEXT DEFAULT 'UNPROCESSED',
                comments_amount INTEGER DEFAULT 0,
                photos_amount INTEGER DEFAULT 0,
                videos_amount INTEGER DEFAULT 0,
                order_status TEXT DEFAULT 'DELIVERED',
                is_rating_participant BOOLEAN DEFAULT FALSE,
                answer TEXT,
                AI_answer TEXT,
                was_AI BOOLEAN DEFAULT FALSE
            )
        """
        self.cursor.execute(sql)
        self.conn.commit()

    def add_review(self, review_data: Dict[str, Any]) -> None:
        columns = ", ".join(review_data.keys())
        placeholders = ":" + ", :".join(review_data.keys())
        sql = f"INSERT INTO reviews ({columns}) VALUES ({placeholders})"
        try:
            self.cursor.execute(sql, review_data)
            self.conn.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Ошибка добавления отзыва: {e}")

    def update_review(self, review_id: str, updated_fields: Dict[str, Any]) -> None:
        set_clause = ", ".join([f"{key}=:{key}" for key in updated_fields])
        sql = f"UPDATE reviews SET {set_clause} WHERE id=:id"
        updated_fields["id"] = review_id
        try:
            self.cursor.execute(sql, updated_fields)
            self.conn.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Ошибка обновления отзыва: {e}")

    def get_reviews_count_by_status(
        self, status_list: List[str] = None, rating_list: List[int] = None
    ) -> int:
        status_list = status_list or ["PROCESSED", "UNPROCESSED"]
        rating_list = rating_list or [4, 5]
        status_str = ", ".join(f"'{s}'" for s in status_list)
        rating_str = ", ".join(str(r) for r in rating_list)
        sql = f"""
            SELECT COUNT(*) FROM reviews
            WHERE status IN ({status_str}) AND rating IN ({rating_str})
        """
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def get_all_reviews(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM reviews")
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_review_by_id(self, review_id: str) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM reviews WHERE id=?", (review_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def delete_review(self, review_id: str) -> None:
        try:
            self.cursor.execute("DELETE FROM reviews WHERE id=?", (review_id,))
            self.conn.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Ошибка удаления отзыва: {e}")

    def close_connection(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
