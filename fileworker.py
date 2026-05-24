import json
from pathlib import Path

from config import settings

REVIEWS_FILE_PATH = settings.reviews_config_path


def create_default_structure():
    default_data = {
        "rating_1": [],
        "rating_2": [],
        "rating_3": [],
        "rating_4": [],
        "rating_5": [],
        "score_list": [],
        "admin_list": settings.admin_ids,
    }
    Path(REVIEWS_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEWS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(default_data, f, ensure_ascii=False, indent=4)


def load_reviews():
    try:
        with open(REVIEWS_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        create_default_structure()
        return load_reviews()


def save_reviews(data):
    with open(REVIEWS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def update_file_stat(rating, path=None):
    path = path or settings.reviews_counter_path
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data[str(rating)] = data.get(str(rating), 0) + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def add_review_to_rating(rating="5", review_text="default review"):
    actual_rating = f"rating_{rating}"
    reviews = load_reviews()
    if actual_rating not in reviews or not isinstance(reviews[actual_rating], list):
        raise KeyError(f"Рейтинг '{rating}' некорректен или не найден.")
    reviews[actual_rating].append(review_text)
    save_reviews(reviews)


def remove_review_from_rating(rating="rating_5", index=-1):
    actual_rating = f"rating_{rating}"
    reviews = load_reviews()
    if actual_rating not in reviews or not isinstance(reviews[actual_rating], list):
        raise KeyError(f"Рейтинг '{rating}' некорректен или не найден.")
    if len(reviews[actual_rating]) > abs(index):
        del reviews[actual_rating][index]
        save_reviews(reviews)
    else:
        raise IndexError(f"Индекс вне диапазона для рейтинга '{rating}'.")


def get_reviews_for_rating(rating="rating_5"):
    reviews = load_reviews()
    return reviews.get(rating, [])


def get_all_reviews():
    return load_reviews()
