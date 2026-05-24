import sqlite3
from typing import List, Dict


class ReviewManager:
    def __init__(self, db_name: str = './data/reviews.db'):
        """ Инициализация соединения с базой данных """
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """ Создание таблицы reviews """
        sql_query = '''
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
        '''
        self.cursor.execute(sql_query)
        self.conn.commit()

    def add_review(self, review_data: Dict[str, any]):
        """ Добавляет новый объект отзыва в базу данных """
        columns = ', '.join(review_data.keys())
        placeholders = ':' + ', :'.join(review_data.keys())
        insert_sql = f'''
            INSERT INTO reviews ({columns}) VALUES ({placeholders})
        '''
        try:
            self.cursor.execute(insert_sql, review_data)
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка добавления отзыва: {e}")

    def update_review(self, review_id: str, updated_fields: Dict[str, any]):
        """ Обновляет данные определенного отзыва """
        set_clause = ", ".join([f"{key}=:{key}" for key in updated_fields])
        update_sql = f'''
            UPDATE reviews SET {set_clause} WHERE id=:id
        '''
        updated_fields['id'] = review_id
        try:
            self.cursor.execute(update_sql, updated_fields)
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка обновления отзыва: {e}")

    def get_reviews_count_by_status(self, status_list = ['PROCESSED','UNPROCESSED'], rating_list = [4,5]):
        """ Возвращает все записи из таблицы reviews """
        select_sql = f'''
            SELECT COUNT(*) FROM reviews where status in ({str(status_list)[1:-1]}) and rating in ({str(rating_list)[1:-1]})
        '''
        
        self.cursor.execute(select_sql)
        result = self.cursor.fetchall()[0][0]

        return result
    
        
    def get_all_reviews(self) -> List[Dict]:
        """ Возвращает все записи из таблицы reviews """
        select_sql = '''
            SELECT * FROM reviews
        '''
        self.cursor.execute(select_sql)
        rows = self.cursor.fetchall()
        column_names = [desc[0] for desc in self.cursor.description]
        result = []
        for row in rows:
            result.append(dict(zip(column_names, row)))
        return result

    def get_review_by_id(self, review_id: str) -> Dict:
        """ Поиск отзыва по уникальному идентификатору """
        select_sql = '''
            SELECT * FROM reviews WHERE id=?
        '''
        self.cursor.execute(select_sql, (review_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        column_names = [desc[0] for desc in self.cursor.description]
        return dict(zip(column_names, row))

    def delete_review(self, review_id: str):
        """ Удаляет запись из базы данных по идентификатору """
        delete_sql = '''
            DELETE FROM reviews WHERE id=?
        '''
        try:
            self.cursor.execute(delete_sql, (review_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка удаления отзыва: {e}")

    def close_connection(self):
        """ Закрывает соединение с базой данных """
        self.conn.close()


if __name__ == "__main__":
    manager = ReviewManager()
    # print(manager.get_reviews_count_by_status(status_list= ['UNPROCESSED']))
    #print(manager.get_review_by_id('017c0d08-8b97-c0e8-b0d3-8a027a12e480'))
    # Пример заполнения базового набора данных
    # reviews = [
    #     {'id': '017c0d08-19b2-3d26-d1a6-fc74fed03408', 'sku': 1945755897, 'text': 'Один раз на пробу...', 'published_at': '2017-06-06T15:17:21.927Z', 'rating': 4},
    #     {'id': '017c0d08-1ff5-0eed-5b4e-27d59d6e1177', 'sku': 1975970391, 'text': 'Для подарка хороший вариант.', 'published_at': '2017-06-07T05:23:01.780Z', 'rating': 5},
    #     # Остальные объекты...
    # ]

    # # Заполнение базы тестовыми объектами
    # for review in reviews:
    #     manager.add_review(review)

    # # Чтение всех отзывов
    # all_reviews = manager.get_all_reviews()
    # print(all_reviews)

    # # Обновляем один из отзывов
    # updated_review = {'id': '017c0d08-19b2-3d26-d1a6-fc74fed03408', 'answer': 'Мы рады, что вам понравилось!', 'was_AI': True}
    # manager.update_review(updated_review['id'], updated_review)

    # # Получаем обновленный отзыв
    # single_review = manager.get_review_by_id('017c0d08-19b2-3d26-d1a6-fc74fed03408')
    # print(single_review)
    
    # # Удаляем конкретный отзыв
    # manager.delete_review('017c0d08-1ff5-0eed-5b4e-27d59d6e1177')

    print(manager.get_reviews_count_by_status(status_list = ['UNPROCESSED'], rating_list = [4,5]))
    # Завершаем работу с базой данных
    manager.close_connection()