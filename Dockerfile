FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Устанавливаем системные зависимости (gcc для нативных пакетов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем конфигурацию uv и lock-файл
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости (без dev, fallback copy hardlink)
RUN uv sync --no-dev --no-cache --link-mode=copy

# Копируем весь проект
COPY . .

# Создаём директорию для данных
RUN mkdir -p /app/data

# Healthcheck (проверка что бот стартует и процесс живой)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD pgrep -f "main.py" || exit 1

# Запуск через uv run (автоматически использует .venv)
CMD ["uv", "run", "--no-dev", "main.py"]
