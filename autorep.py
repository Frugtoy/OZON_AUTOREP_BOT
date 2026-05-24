from database_worker import ReviewManager
from random import choice
import asyncio
import json
from ozon_api import count_reviews, list_reviews, change_review_status, create_comment, info_review
from fileworker import update_file_stat
# TODO : 1) Проверить необходимость пометки ответов после обработки. 2)Реализовать функции

# В json файле записаны ответные комментарии для оценок 4 и 5


async def update_db():
    '''Обновляем БД новыми отзывами'''
    # Инициализируем БД
    
    manager = ReviewManager()
    # Считываем все отзывы из БД
    all_reviews = manager.get_all_reviews()
    # unprcsd_reviews_cnt = manager.get_reviews_count_by_status(status_list= ['UNPROCESSED'])
    # if unprcsd_reviews_cnt > unprocessed_responces_limit:
    #     manager.close_connection()
    #     return
    # Узнаем кол-во новых отзывов
    #print(all_reviews)
    new_reviews_number = count_reviews()['total'] - len(all_reviews)
    # Если есть новые отзывы, добавим их в БД
    # Берем ID последнего отзыва:
    last_id = all_reviews[-1]['id']
    while new_reviews_number:
        print(f"ВНИМАНИЕ. Новые отзывы: {new_reviews_number} шт.")
        reviews = list_reviews(last_id=last_id, limit=100, status="ALL")['reviews']
        for review in reviews:
          manager.add_review(review)
        # print(f"Добавили в БД отзывы: {'; '.join([review['id'] for review in reviews])}")
        # И проверяем в цикле на новые отзывы
        all_reviews = manager.get_all_reviews()
        new_reviews_number = count_reviews()['total'] - len(all_reviews)
        last_id = all_reviews[-1]['id']

    # Закроем соединение с БД
    manager.close_connection()

async def check_unproceed_reviews(ratings=[]):
    '''Проверяем, есть ли в бд неотвеченные отзывы по рейтингам '''
    # Для начала обновим записи БД
    #await update_db()
    # Инициализируем БД
    manager = ReviewManager()
    # Считываем все отзывы из БД 
    all_reviews = manager.get_all_reviews()
    # Закроем соединение с БД
    manager.close_connection()
    unprocessed_reviews = [x for x in all_reviews if x['rating'] in ratings and x['status'] == 'UNPROCESSED']
    print(f"Есть отзывы необработанные? {unprocessed_reviews}")
    if unprocessed_reviews:
        print('ВНИМАНИЕ! В БД есть необработанные отзывы')
        return unprocessed_reviews
    print('В БД нет необработанных отзывов')
    return False


async def load_unproceed_reviews_by_rating(rating: str):
    '''Загружает (insert) в базенку отзывы по рейтингу по апи'''
    pass


async def get_unproceed_reviews_by_rating(rating: list) -> list:
    reviews = await check_unproceed_reviews(rating)
    return reviews if reviews else []


async def mark_review(review_id):
    '''Помечает отзыв как обработанный'''
    # Инициализируем БД
    manager = ReviewManager()
    # Считываем все отзывы из БД
    review = manager.get_review_by_id(review_id)
    # Закроем соединение с БД
    manager.update_review(review_id, {"status": "PROCESSED"})
    manager.close_connection()
    change_review_status([review_id], 'PROCESSED')


async def generate_response(review_id: str, data):
    '''Отправляет ответ по апи и грузит его в бд'''
    # Инициализируем БД
    manager = ReviewManager()
    # Считываем все отзывы из БД
    review = manager.get_review_by_id(review_id)
    # Берем ответ из json
    rating = review['rating']
    #TODO сделать рандомный выбор индекса от длины
    response = choice(data[f"rating_{rating}"])
    manager.update_review(review_id, {"answer": response,"status":"PROCESSED"})
    manager.close_connection()
    create_comment(review_id, response)
    await asyncio.sleep(3) 

async def new_generate_response(review: str, data):
    '''Отправляет ответ по апи и грузит его в бд'''
    # Считываем все отзывы из БД
    # Берем ответ из json
    rating = review['rating']
    #TODO сделать рандомный выбор индекса от длины
    response = choice(data[f"rating_{rating}"])
    create_comment(review['id'], response)
    await asyncio.sleep(3) 
    
async def proceed_review(review_id: str):
    '''отправляет ответ на отзыв по апи, созраняет его в базенку, помечает отзыв обработанным (generete_response + mark_review)'''
    await generate_response(review_id)
    await mark_review(review_id)
    
    

from ozon_api import count_reviews, list_reviews, change_review_status, create_comment, info_review

async def get_rewiews_by_rating(rating_list, last_id = None):
    raw = list_reviews(last_id = last_id,sort_dir = "DESC", status = "UNPROCESSED")
    
    # Защита от пустого ответа API
    if not raw or 'reviews' not in raw:
        print(f"[WARN] API вернул пустой ответ или нет reviews: {raw}")
        return []
    
    rews = [i for i in raw['reviews'] if int(i["rating"]) in rating_list]
    if rews:
        return rews
    else:
        # Проверяем, есть ли last_id для следующей страницы
        next_last_id = raw.get('last_id')
        if not next_last_id:
            print(f"[INFO] Больше нет отзывов для обработки (last_id отсутствует)")
            return []
        try:
            return await get_rewiews_by_rating(rating_list, last_id=next_last_id)
        except Exception as E:
            print(f"[ERROR] Ошибка при рекурсивном запросе: {E}")
            return []
            

async def proceed_reviews(reviews_config_path = 'data/reviews_config.json' ):
    with open(reviews_config_path, 'r', encoding='utf-8') as file:
        # Прочтем их
        data = json.load(file)

    rating_list  = data['score_list']
    rews = await get_rewiews_by_rating(rating_list, last_id = None)
    for rew in  rews:
        await new_generate_response(rew,data)
        await update_file_stat(str(rew['rating']))
        await asyncio.sleep(0.2)
        
    
   
    # data = json.load(file)
    # rews = []
    # offset = 0
    # while not rews:
    #     rews = get_rewiews_by_rating([6],offset)
    #     offset +=100
    #     print(offset)
    # print(count_reviews())
    
   
async def run(reviews_config_path = 'data/reviews_config.json' ):
    while True:
        await proceed_reviews(reviews_config_path)


if __name__ == "__main__":
    async def main():
        #await(run(reviews_config_path = 'reviews_config.json'))
        await run()

    asyncio.run(main())

# bot->autorrep->check_unproceed_reviews->OPT[load_unproceed_reviews_by_rating]->load_unproceed_reviews_by_rating: list_of_rev_id:[{id, response}]
# res = get_unproceed_reviews_by_rating(5)
# print(res)
# list_of_rev_id[i]->API_ANSWER[id,response]->MARK_AS_PROCEEDED[id](DATABASE+API) = proceed_review

