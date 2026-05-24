import json
import os

# Путь к файлу с отзывами
REVIEWS_FILE_PATH = './data/reviews_config.json'

def create_default_structure():
    """Создает стандартный JSON-файл с пустой структурой отзывов"""
    default_data = {
        "rating_1": [],      # Отзывы с одной звездой
        "rating_2": [],      # Отзывы с двумя звездами
        "rating_3": [],      # Отзывы с тремя звездами
        "rating_4": [],      # Отзывы с четырьмя звездами
        "rating_5": []       # Отзывы с пятью звездами
    }
    with open(REVIEWS_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(default_data, file, ensure_ascii=False, indent=4)

def load_reviews():
    """Загружает данные из файла с отзывами"""
    try:
        with open(REVIEWS_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        create_default_structure()
        return load_reviews()

def save_reviews(data):
    """Сохраняет данные в файл с отзывами"""
    with open(REVIEWS_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


async def update_file_stat(rating, path ='data/rewiews_counter.json'):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        data[rating] +=1
        
    with open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(data))
        
def add_review_to_rating(rating="5", review_text="default review"):
    """ Добавляет новый отзыв в указанный рейтинг. Аргументы: - rating: Число звёзд (например, "5"). Префикс "rating_" добавляется автоматически. - review_text: текст отзыва. """
    actual_rating = f'rating_{rating}'
    reviews = load_reviews()
    if actual_rating not in reviews or not isinstance(reviews[actual_rating], list):
        raise KeyError(f"Рейтинг '{rating}' некорректен или не найден.")
    
    reviews[actual_rating].append(review_text)
    save_reviews(reviews)

def remove_review_from_rating(rating="rating_5", index=-1):
    """ Удаляет отзыв из указанного рейтинга по индексу. Аргументы: - rating: название ключа ("rating_X"), где X — число звёзд. - index: индекс отзыва, который надо удалить (-1 для последнего элемента). """
    actual_rating = f'rating_{rating}'
    reviews = load_reviews()
    if actual_rating not in reviews or not isinstance(reviews[actual_rating], list):
        raise KeyError(f"Рейтинг '{rating}' некорректен или не найден.")
    
    if len(reviews[actual_rating]) > abs(index):
        del reviews[actual_rating][index]
        save_reviews(reviews)
    else:
        raise IndexError(f"Индекс вне диапазона для рейтинга '{rating}'.")

def get_reviews_for_rating(rating="rating_5"):
    """ Возвращает список отзывов для указанного рейтинга. Аргументы: - rating: Название ключа ("rating_X"). """
    actual_rating = f'rating_{rating}'
    reviews = load_reviews()
    print(rating,reviews)
    return reviews.get(rating, [])

def get_all_reviews():
    """ Возвращает все доступные отзывы из файла. """
    return load_reviews()