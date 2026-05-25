import asyncio
import json
import logging
from pathlib import Path
from random import choice
from typing import List, Dict, Any, Tuple

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
        """Синхронизация: подгрузить новые отзывы из Ozon в локальную БД."""
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

    # ─── Ozon Auto-Reply Batch ───────────────────────────────

    async def process_batch(self) -> Tuple[int, int, int]:
        """
        Одна итерация автоответчика:
        - Запрашивает UNPROCESSED отзывы из Ozon
        - Отвечает только на те, что подходят под score_list
        - Возвращает (успешных, пропущено по рейтингу, ошибок)
        """
        from api import list_reviews, create_comment

        config = self.load_config()
        score_list = config.get("score_list", [])
        if not score_list:
            logger.info("score_list пуст — не на что отвечать")
            return 0, 0, 0

        # Пауза между запросами к Ozon API
        await asyncio.sleep(1)

        batch = list_reviews(status="UNPROCESSED", limit=100)
        reviews = batch.get("reviews", [])

        if not reviews:
            logger.debug("Нет UNPROCESSED отзывов")
            return 0, 0, 0

        success = skip = errors = 0

        with ReviewManager() as manager:
            for review in reviews:
                rid = review.get("id")
                rating = review.get("rating")

                if rating not in score_list:
                    logger.debug(f"Отзыв {rid} rating={rating} — пропускаем (не в score_list)")
                    skip += 1
                    continue

                answer = self.get_random_response(rating, config)
                logger.info(f"Отвечаем на отзыв {rid} (rating={rating})")

                try:
                    resp = create_comment(rid, answer)
                    logger.debug(f"create_comment response: {resp}")

                    # Обновляем локальную БД
                    manager.update_review(rid, {
                        "status": "PROCESSED",
                        "answer": answer,
                    })
                    await self.update_counter(rating)
                    success += 1
                    await asyncio.sleep(1)  # rate-limit между create_comment

                except Exception as exc:
                    logger.error(f"Ошибка ответа на отзыв {rid}: {exc}")
                    # Не помечаем как PROCESSED — при следующем запросе попробуем снова
                    errors += 1
                    # Небольшая пауза перед следующей попыткой
                    await asyncio.sleep(2)

        return success, skip, errors

    async def process_batches(self, max_batches: int = 10) -> Tuple[int, int, int]:
        """
        Обрабатывает до max_batches итераций подряд.
        Останавливается, если batch пустой.
        Возвращает (успешных, пропущено, ошибок).
        """
        total_success = total_skip = total_errors = 0
        for _ in range(max_batches):
            s, sk, e = await self.process_batch()
            total_success += s
            total_skip += sk
            total_errors += e
            # Если batch пустой — выходим, больше пока нечего обрабатывать
            if s == 0 and sk == 0 and e == 0:
                break
        return total_success, total_skip, total_errors
