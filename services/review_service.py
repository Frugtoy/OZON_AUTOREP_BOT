import asyncio
import json
import logging
from pathlib import Path
from random import choice
from typing import List, Dict, Any

from db import ReviewManager
from config import settings

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self):
        self.config_path = settings.reviews_config_path
        self.counter_path = settings.reviews_counter_path
        self._ensure_counter()

    def _ensure_counter(self) -> None:
        if not Path(self.counter_path).exists():
            Path(self.counter_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.counter_path, "w", encoding="utf-8") as f:
                json.dump({"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}, f)

    def load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, data: Dict[str, Any]) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    async def update_db(self) -> None:
        from api import count_reviews, list_reviews

        with ReviewManager() as manager:
            all_reviews = manager.get_all_reviews()
            total_api = count_reviews().get("total", 0)
            new_count = total_api - len(all_reviews)

            if new_count <= 0:
                logger.info("Нет новых отзывов для загрузки")
                return

            # При пустой БД загружаем с начала (без last_id)
            last_id = all_reviews[-1]["id"] if all_reviews else None
            loaded_total = 0

            while new_count > 0:
                logger.info(f"Загрузка новых отзывов: осталось ~{new_count} шт.")

                if last_id:
                    reviews_batch = list_reviews(last_id=last_id, limit=100, status="ALL")
                else:
                    reviews_batch = list_reviews(limit=100, status="ALL")

                batch = reviews_batch.get("reviews", [])
                if not batch:
                    logger.warning("API вернул пустой список, прерываем синхронизацию")
                    break

                for review in batch:
                    manager.add_review(review)
                    loaded_total += 1

                all_reviews = manager.get_all_reviews()
                total_api = count_reviews().get("total", 0)
                new_count = total_api - len(all_reviews)
                last_id = all_reviews[-1]["id"] if all_reviews else None

            logger.info(f"Синхронизация завершена, загружено {loaded_total} отзывов")

    async def get_unprocessed(self, ratings: List[int]) -> List[Dict[str, Any]]:
        with ReviewManager() as manager:
            reviews = manager.get_all_reviews()
        return [r for r in reviews if r["rating"] in ratings and r["status"] == "UNPROCESSED"]

    def get_random_response(self, rating: int, config: Dict[str, Any]) -> str:
        key = f"rating_{rating}"
        responses = config.get(key, [])
        if not responses:
            logger.warning(f"Нет ответов для рейтинга {rating}")
            return "Спасибо за ваш отзыв!"
        return choice(responses)

    async def update_counter(self, rating: int) -> None:
        with open(self.counter_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data[str(rating)] = data.get(str(rating), 0) + 1
            f.seek(0)
            json.dump(data, f)
            f.truncate()
