import requests
import logging
from typing import Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import settings

logger = logging.getLogger(__name__)

base_url = "https://api-seller.ozon.ru/"


def _headers() -> Dict[str, str]:
    return {
        "Client-Id": settings.client_id,
        "Api-Key": settings.api_token,
        "Content-Type": "application/json",
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=False,
)
def _post(endpoint: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
    url = f"{base_url}{endpoint}"
    try:
        response = requests.post(url, headers=_headers(), json=payload or {}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # 4xx ошибки — не retry, но логируем
        logger.error(f"Ozon API HTTP error [{endpoint}]: {e.response.status_code} — {e.response.text[:200]}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Ozon API network error [{endpoint}]: {e}")
        raise


def create_comment(review_id: str, text: str, parent_comment_id: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "mark_review_as_processed": True,
        "review_id": review_id,
        "text": text,
    }
    if parent_comment_id:
        payload["parent_comment_id"] = parent_comment_id
    return _post("/v1/review/comment/create", payload)


def delete_comment(comment_id: str) -> Dict[str, Any]:
    return _post("/v1/review/comment/delete", {"comment_id": comment_id})


def list_comments(
    review_id: str, limit: int = 100, offset: int = 0, sort_dir: str = "ASC"
) -> Dict[str, Any]:
    """
        Получает список отзывов с возможностью фильтрации.
        
        :param limit: Количество отзывов в ответе
        :param last_id: Последний ID отзыва на предыдущей странице
        :param sort_dir: Направление сортировки ("ASC"/"DESC")
        :param status: Фильтр по статусу ("ALL"/"UNPROCESSED"/"PROCESSED")
        :return: Список отзывов или ошибка
    """
    return _post(
        "/v1/review/comment/list",
        {"limit": limit, "offset": offset, "review_id": review_id, "sort_dir": sort_dir},
    )


def change_review_status(review_ids: list, status: str) -> Dict[str, Any]:
    return _post("/v1/review/change-status", {"review_ids": review_ids, "status": status})


def count_reviews() -> Dict[str, Any]:
    return _post("/v1/review/count")


def info_review(review_id: str) -> Dict[str, Any]:
    return _post("/v1/review/info", {"review_id": review_id})


def list_reviews(
    limit: int = 100,
    last_id: Optional[str] = None,
    sort_dir: str = "ASC",
    status: str = "UNPROCESSED",
) -> Dict[str, Any]:
    payload = {"limit": limit, "sort_dir": sort_dir, "status": status}
    if last_id:
        payload["last_id"] = last_id
    return _post("/v1/review/list", payload)
