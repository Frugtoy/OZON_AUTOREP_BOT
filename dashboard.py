import pandas as pd 
from database_worker import ReviewManager
import json



def load_to_df():
     manager = ReviewManager()
     return pd.DataFrame(manager.get_all_reviews())


def get_bd_stat_():
    df = load_to_df()
    df['status'] = df['status'].apply(lambda x: x.replace('UNPROCESSED','Необработанные'))
    df['status'] = df['status'].apply(lambda x: x.replace('PROCESSED','Обработанные'))
    return str(df.groupby(['status','rating']).id.count())

def get_bd_stat():
     df = load_to_df()
     df['status'] = df['status'].apply(lambda x: x.replace('UNPROCESSED','Необработанные'))
     df['status'] = df['status'].apply(lambda x: x.replace('PROCESSED','Обработанные'))
     grouped = df.groupby(['status', 'rating'])['id'].count().reset_index()
     output_lines = []

     # Добавляем категорию НЕОБРАБОТАННЫЕ
     output_lines.append('⚠️ Необработанные:')
     for index, row in grouped.query("status == 'Необработанные'").iterrows():
          output_lines.append(f'{row["rating"]}: {row["id"]}')

     # Добавляем пустую строку для разделения секций
     output_lines.append('')

     # Добавляем категорию ОБРАБОТАННЫЕ
     output_lines.append('🟢 Обработанные:')
     for index, row in grouped.query("status == 'Обработанные'").iterrows():
          output_lines.append(f'{row["rating"]}: {row["id"]}')

     # Объединяем строки в единую строку с переносами строк
     formatted_output = '\n'.join(output_lines)

     return formatted_output

