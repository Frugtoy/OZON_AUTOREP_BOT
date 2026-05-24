FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Устанавливаем системные зависимости (gcc для нативных пакетов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем конфигурацию uv и lock-файл
COPY pyproject.toml uv.lock ./

# Создаём venv и устанавливаем зависимости (без dev)
RUN uv sync --no-dev --no-cache

# Копируем весь проект
COPY . .

# Создаём директорию для данных
RUN mkdir -p /app/data

# Запуск через uv run (автоматически использует .venv)
CMD ["uv", "run", "--no-dev", "main.py"]
