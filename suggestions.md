# Рекомендации по улучшению проекта

## 1. Структура проекта

Текущая плоская структура хороша для прототипа, но усложняет поддержку.
Рекомендуется разбить на модули:

```
ozon_autorep_bot/
├── bot/                 # Telegram бот (handlers, keyboards, middlewares)
│   ├── __init__.py
│   ├── handlers.py
│   ├── keyboards.py
│   └── middlewares.py
├── api/                 # Ozon API клиент
│   ├── __init__.py
│   └── ozon.py
├── ai/                  # LLM генераторы ответов
│   ├── __init__.py
│   ├── gigachat.py      # GigaChat (облачный)
│   └── local.py         # Локальная LLM (Ollama/llama.cpp)
├── db/                  # База данных
│   ├── __init__.py
│   ├── models.py
│   └── manager.py
├── config/              # Настройки (pydantic-settings)
│   ├── __init__.py
│   ├── settings.py
│   └── logging.py
├── services/            # Бизнес-логика
│   ├── __init__.py
│   └── review_service.py
├── data/                # SQLite + JSON конфиги
├── .env
├── .env-example
├── .gitignore
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── main.py              # Точка входа
```

## 2. Конфигурация через Pydantic-Settings

Вместо ручного `os.getenv()` во всех файлах — централизованный конфиг с валидацией:

- Типизация (int для admin_ids, bool для флагов)
- Валидация при старте (нет BOT_TOKEN = краш с понятной ошибкой)
- `.env` файл подключается автоматически
- Поддержка списков через запятую в строке

## 3. Логирование

Сейчас только `print()`. Нужно:
- Логи в файл (`data/logs/bot.log`)
- Ротация логов (чтобы не забивать диск)
- Структурированный формат: `2024-01-15 10:30:00 | bot | INFO | Сообщение`

## 4. CI/CD (GitHub Actions)

```yaml
- lint: ruff check + ruff format --check
- test: pytest (юнит-тесты для сервисов)
- build: docker build + push to GHCR
```

Добавить в `pyproject.toml`:
- `ruff` — линтер и форматтер
- `pytest` + `pytest-asyncio` — тесты
- `mypy` — типизация

## 5. Локальная LLM (Ollama)

**Зачем:** генерация персонализированных ответов без облака.
**Модели:**
- `qwen2.5:7b` — отличный русский, ~4GB RAM
- `saiga` — специально дообучен для русского диалога
- `mistral:7b` — универсальный

**Интеграция:**
```python
class LocalLLM:
    async def generate_response(
        self,
        rating: int,
        review_text: str,
        product_category: Optional[str] = None
    ) -> str:
        # Персонализированный промпт на основе рейтинга и категории
        ...
```

**Docker Compose:**
```yaml
services:
  bot:
    build: .
    depends_on: [ollama]
  ollama:
    image: ollama/ollama
    volumes: [ollama_models:/root/.ollama]
```

## 6. Кэширование ответов LLM

Сохранять сгенерированные ответы в БД (хэш от текста отзыва → ответ).
Повторные похожие отзывы — мгновенный ответ без вызова LLM.

## 7. Обработка ошибок API

Сейчас если Ozon API недоступен — бот падает.
Нужен `tenacity` для retry с backoff:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def list_reviews(...):
    ...
```

## 8. Админ-лист в .env

Сейчас `sudo = [438662734]` захардкожен. Перенести в `ADMIN_IDS` в `.env`:
```env
ADMIN_IDS=438662734,123456789
```

## 9. Дашборд улучшений

- Статистика по категориям товаров
- Распределение отзывов по времени
- Среднее время ответа
- Топ-5 товаров с проблемами

## 10. Миграции БД

Сейчас `create_table()` просто `IF NOT EXISTS`.
Для эволюции схемы — Alembic или хотя бы версионирование через `PRAGMA user_version`.
