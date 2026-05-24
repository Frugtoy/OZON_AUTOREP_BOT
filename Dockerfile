# Используем официальную легковесную версию образа Python
FROM python:3.11-slim-buster

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем необходимые файлы внутрь контейнера
COPY . .

# Устанавливаем зависимости из файла requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем приложение
CMD ["python", "bot.py"]