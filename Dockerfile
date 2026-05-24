FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Копируем код
COPY . .

# Создаём директории для данных
RUN mkdir -p /app/data/logs

CMD ["python", "main.py"]
