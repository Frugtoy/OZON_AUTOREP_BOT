import requests
import json
from dotenv import load_dotenv
import os
load_dotenv()

# Настройки прокси (если включен флаг)
USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
PROXY_LIST = os.getenv('PROXY_LIST', '')
PROXIES = None
if USE_PROXY and PROXY_LIST:
    # Поддерживаем формат: http://user:pass@host:port или несколько через запятую
    proxies_raw = [p.strip() for p in PROXY_LIST.split(',') if p.strip()]
    if proxies_raw:
        proxy_url = proxies_raw[0]
        PROXIES = {
            'http': proxy_url,
            'https': proxy_url
        }

# Настройки API
base_url = 'https://api-seller.ozon.ru/'
headers = {
    'Client-Id': os.getenv('CLIENT_ID'),
    'Api-Key': os.getenv('API_TOKEN'),
    'Content-Type': 'application/json'
}


def create_comment(review_id, text, parent_comment_id=None):
    """
    Создание комментария на отзыв.
    
    :param review_id: Идентификатор отзыва
    :param text: Текст комментария
    :param parent_comment_id: Идентификатор родительского комментария (необязательно)
    :return: comment_id или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        "mark_review_as_processed": True,
        "review_id": review_id,
        "text": text
    }
    if parent_comment_id:
        payload["parent_comment_id"] = parent_comment_id
        
    response = requests.post(f'{base_url}/v1/review/comment/create', headers=headers, data=json.dumps(payload), proxies=PROXIES)
    return response.json()

def delete_comment(comment_id):
    """
    Удаляет комментарий на отзыв.
    
    :param comment_id:param Идентификатор комментария
    :return: Результат удаления или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {"comment_id": comment_id}
    response = requests.post(f'{base_url}/v1/review/comment/delete', headers=headers, data=json.dumps(payload), proxies=PROXIES)
    return response.json()

def list_comments(review_id, limit=100, offset=0, sort_dir="ASC"):
    """
    Возвращает список комментариев на отзыв.
    
    :param review_id: Идентификатор отзыва
    :param limit: Количество возвращаемых записей (от 20 до 100)
    :param offset: Смещение выборки
    :param sort_dir: Направление сортировки ("ASC"/"DESC")
    :return: Список комментариев или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        "limit": limit,
        "offset": offset,
        "review_id": review_id,
        "sort_dir": sort_dir
    }
    response = requests.post(f'{base_url}/v1/review/comment/list', headers=headers, data=json.dumps(payload), proxies=PROXIES)
    return response.json()

def change_review_status(review_ids, status):
    """
    Меняет статус одного или нескольких отзывов.
    
    :param review_ids: Массив идентификаторов отзывов
    :param status: Статус ('PROCESSED'/'UNPROCESSED')
    :return: Ответ сервера или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        "review_ids": review_ids,
        "status": status
    }
    response = requests.post(f'{base_url}/v1/review/change-status', headers=headers, data=json.dumps(payload), proxies=PROXIES)
    return response.json()

def count_reviews():
    """
    Получает количество отзывов по каждому статусу.
    
    :return: Объект с количеством отзывов или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.post(f'{base_url}/v1/review/count', headers=headers, proxies=PROXIES)
    return response.json()

def info_review(review_id):
    """
    Получает подробную информацию об одном отзыве.
    
    :param review_id: Идентификатор отзыва
    :return: Детали отзыва или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {"review_id": review_id}
    response = requests.post(f'{base_url}/v1/review/info', headers=headers, data=json.dumps(payload), proxies=PROXIES)
    return response.json()

def list_reviews(limit=100, last_id=None, sort_dir="ASC", status="UNPROCESSED"):
    """
    Получает список отзывов с возможностью фильтрации.
    
    :param limit: Количество отзывов в ответе
    :param last_id: Последний ID отзыва на предыдущей странице
    :param sort_dir: Направление сортировки ("ASC"/"DESC")
    :param status: Фильтр по статусу ("ALL"/"UNPROCESSED"/"PROCESSED")
    :return: Список отзывов или ошибка
    """
    # headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        "limit": limit,
        "sort_dir": sort_dir,
        "status": status
    }
    if last_id:
        payload['last_id'] = last_id
    response = requests.post(f'{base_url}/v1/review/list', headers=headers, data=json.dumps(payload), proxies=PROXIES)

    return response.json()


# # Создать новый комментарий на отзыв
# response_create = create_comment("REVIEWS_ID_HERE", "Спасибо за ваш отзыв!")
# print(response_create)

# # Удалить комментарий
# response_delete = delete_comment("COMMENT_ID_HERE")
# print(response_delete)

# Получить список комментариев к определенному отзыву
# response_list_comments = list_comments("REVIEWS_ID_HERE")
# print(count_reviews())

# # Изменить статус отзыва
# response_change_status = change_review_status(["REVIEWS_ID_HERE"], "PROCESSED")
# print(response_change_status)

# # Посмотреть общее количество отзывов
# response_count = count_reviews()
# print(response_count)

# # Получить информацию конкретного отзыва
# response_info = info_review("REVIEWS_ID_HERE")
# print(response_info)

# Просмотр общего списка отзывов
# response_list = list_reviews(limit=100, last_id='017c0d08-1ebb-e411-e270-91ff6f403f6c', sort_dir="ASC", status="UNPROCESSED")
# print(response_list['reviews'])
# response_info = info_review("017c0d08-1ebb-e411-e270-91ff6f403f6c")
# print(response_info)
# # Посмотреть общее количество отзывов
# response_count = count_reviews()
# print(response_count)
# response_list = list_reviews(limit=100)
# print(response_list['reviews'])
# print(list_comments('017c0d08-8b97-c0e8-b0d3-8a027a12e480'))