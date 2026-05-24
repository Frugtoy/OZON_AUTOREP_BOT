# Ozon AutoReply Bot

Автоматический ответчик на отзывы маркетплейса Ozon через Telegram-бота.  
Бот мониторит неотвеченные отзывы, генерирует персонализированные ответы через LLM (GigaChat или локальную модель через Ollama) и публикует их от имени продавца.

---

## 🚀 Быстрый старт (Docker)

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Frugtoy/OZON_AUTOREP_BOT.git
cd OZON_AUTOREP_BOT

# 2. Скопируй и заполни конфигурацию
cp .env.example .env
# → отредактируй .env (токены, прокси)

# 3. Запусти
uv sync            # локальная установка зависимостей
uv run main.py     # локальный запуск

# или через Docker
docker compose up -d
```

---

## 📦 Установка

### Вариант A: Локально через `uv` (рекомендуется)

```bash
# Установи uv (если ещё нет)
curl -LsSf https://astral.sh/uv/install.sh | sh

# В директории проекта
uv sync           # создаст .venv и установит зависимости из uv.lock
uv run main.py    # запуск
```

**Полезные команды uv:**
```bash
uv sync --dev          # + dev-зависимости (pytest, ruff, mypy)
uv run --dev pytest    # запуск тестов
uv run --dev ruff check .   # линтинг
uv add <пакет>         # добавить зависимость
uv lock                # обновить lock-файл после изменения pyproject.toml
```

### Вариант B: Docker

```bash
docker compose build --no-cache
docker compose up -d
docker compose logs -f bot
```

**Остановка:**
```bash
docker compose down
```

### Вариант C: pip (legacy)

```bash
pip install -r requirements.txt
python main.py
```

> **Примечание:** `requirements.txt` оставлен для совместимости. Основной способ — `uv sync` с `uv.lock` (детерминированные версии, быстрее).

---

## ⚙️ Конфигурация

Скопируй `.env.example` → `.env` и заполни переменные.

### Обязательные переменные

| Переменная | Где взять | Описание |
|-----------|-----------|----------|
| `API_TOKEN` | [Ozon Seller → API-ключи](https://seller.ozon.ru/app/settings/api-keys) | Токен доступа к Ozon API |
| `CLIENT_ID` | Там же | ID клиента Ozon |
| `GIGACHAT_CREDENTIALS` | [Sber GigaChat](https://developers.sber.ru/studio/workspace) | Ключ для облачного LLM |
| `BOT_TOKEN` | [@BotFather](https://t.me/botfather) | Токен Telegram-бота |

### Прокси для Telegram (из России)

Если `api.telegram.org` недоступен на сервере, включите прокси:

```env
# Включить прокси
USE_BOT_PROXY=true

# Можно указать несколько через запятую — бот попробует по очереди
# (fallback на следующий, если текущий упал)
BOT_PROXY_LIST=http://user:pass@proxy1:8080,socks5://user:pass@proxy2:1080

# IPv6 — квадратные скобки обязательны (добавляются автоматически):
# http://user:pass@[2a0f:...:994]:8080
```

**Где купить прокси за рубли:**
- [Proxy6.net](https://proxy6.net) — IPv4/IPv6/MTProto, от ~50₽/неделю
- [Proxy-Seller.io](https://proxy-seller.io) — SOCKS5/HTTP, есть фильтр "для Telegram"
- [Proxys.io](https://proxys.io/ru) — мобильные, резидентские, 50 способов оплаты

### Дополнительные настройки

```env
# Администраторы бота (через запятую)
ADMIN_IDS=438662734,123456789

# Пути к данным
DB_PATH=./data/reviews.db
REVIEWS_CONFIG_PATH=./data/reviews_config.json
REVIEWS_COUNTER_PATH=./data/rewiews_counter.json

# SSL для GigaChat (по умолчанию true, false только для отладки!)
GIGACHAT_VERIFY_SSL=true
```

---

## 🏗️ Архитектура

```
ozon_autorep_bot/
├── bot/              # Telegram (aiogram): handlers, inline-клавиатуры, FSM
│   └── handlers.py
├── api/              # Ozon Seller API клиент (requests + tenacity retry)
│   └── ozon.py
├── ai/               # LLM генераторы ответов
│   ├── gigachat.py   # Облачный GigaChat (Sber)
│   └── local.py      # Локальная модель через Ollama (qwen2.5:7b)
├── db/               # SQLite: хранение отзывов
│   └── manager.py
├── services/         # Бизнес-логика: синхронизация, подбор ответов, статистика
│   └── review_service.py
├── config/           # Конфигурация (pydantic-settings) + логирование
│   ├── settings.py
│   └── logging.py
├── main.py           # Точка входа
├── fileworker.py     # JSON-конфиги (rating_1..5, score_list, admin_list)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml    # Зависимости + инструменты (ruff, pytest, mypy)
├── uv.lock           # Lock-файл uv (детерминированные версии)
└── .python-version   # 3.12
```

### Поток данных

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│  Ozon API   │────→│ api/ozon │────→│ db/manager  │──┐
│ (отзывы)    │     │          │     │ (SQLite)    │  │
└─────────────┘     └──────────┘     └─────────────┘  │
                                                     │
┌─────────────┐     ┌──────────────┐   ┌──────────┐  │
│ Telegram    │────→│ bot/handlers │──→│ services │←─┘
│ (админ)     │     │ (aiogram FSM)│   │          │
└─────────────┘     └──────────────┘   └──────────┘
                                             │
                                       ┌─────┴─────┐
                                       │  ai/       │
                                       │ GigaChat / │
                                       │ Ollama     │
                                       └───────────┘
                                             │
                                       ┌─────▼─────┐
                                       │ Ozon API  │
                                       │ (ответы)  │
                                       └───────────┘
```

1. **Синхронизация:** `services/review_service.py` → `api/ozon.py` → загружает отзывы в SQLite
2. **Telegram:** админ выбирает рейтинг → `bot/handlers.py` → `services` → `ai/` генерирует ответ → `api/ozon.py` публикует
3. **AI:** GigaChat (облако) или Ollama (локально, через Docker Compose)

---

## 💬 Использование (Telegram UI)

Запусти бота и отправь `/start`. Доступные команды через inline-кнопки:

| Кнопка | Что делает |
|--------|-----------|
| **Настройка конфига** | Добавить/удалить отзывы по рейтингу, фильтровать рейтинги |
| **Посмотреть конфиг** | Текущие активные рейтинги и тексты отзывов |
| **Настройка администрации** | Добавить/удалить администраторов бота |
| **Запустить автоматические ответы** | Бот начинает отправлять случайные отзывы в чат каждые 5 сек (демо) |
| **Остановить автоматические ответы** | Останавливает демо-режим |
| **Статистика** | Счётчики отзывов по рейтингам |

> **Важно:** Права администратора (`ADMIN_IDS`) требуются для управления конфигом и админами. Обычные пользователи видят только приветствие.

---

## 🛠️ Разработка

### Добавить новую inline-кнопку и сценарий

Все сценарии построены по одной схеме: **кнопка → FSM-состояние → ввод → обработка → выход**.

#### 1. Состояние FSM

```python
# bot/handlers.py
class Form(StatesGroup):
    # ... существующие состояния ...
    MY_NEW_FEATURE = State()
```

#### 2. Кнопка в меню

```python
kb = InlineKeyboardBuilder()
kb.button(text="Моя новая фича", callback_data="my_new_feature")
kb.adjust(1)
await callback.message.edit_text("Выберите действие:", reply_markup=kb.as_markup())
```

#### 3. Обработка кнопки

```python
@router.callback_query(F.data == "my_new_feature")
async def my_feature_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("Нужны права администратора.")
        return
    await state.set_state(Form.MY_NEW_FEATURE)
    await callback.message.edit_text("Введите данные:")
```

#### 4. Обработка ввода

```python
@router.message(Form.MY_NEW_FEATURE)
async def process_my_feature(message: Message, state: FSMContext):
    user_input = message.text.strip()
    # ... валидация и бизнес-логика ...
    await state.clear()
    await message.answer(f"✅ Сохранено: {user_input}")
```

### Существующие сценарии (для примера)

| Сценарий | Кнопка | Состояние | Что вводится |
|----------|--------|-----------|--------------|
| Добавить отзыв | `add_review` → выбор рейтинга | `Form.ADD_REVIEW_TEXT` | Текст отзыва |
| Удалить отзыв | `delete_review` → выбор рейтинга → выбор текста | — | — (клики) |
| Фильтр рейтинга | `filter_rating` → добавить/удалить | `Form.FILTER_RATING_ACTION` | Число 1–5 |
| Добавить админа | `add_admin` | `Form.ADMIN_ADD_USER` | `chat_id` |
| Удалить админа | `remove_admin` | `Form.ADMIN_REMOVE_USER` | `chat_id` |

### Добавить новый LLM-провайдер

```python
# ai/new_provider.py
class NewProvider:
    async def generate(self, rating: int, review_text: str, category=None) -> str:
        # ... реализация ...
        return "Ответ"
```

```python
# ai/__init__.py
from .new_provider import NewProvider
__all__ = ["GigaChatGenerator", "LocalLLM", "NewProvider"]
```

### Добавить метод Ozon API

```python
# api/ozon.py
def new_ozon_method(param: str) -> Dict[str, Any]:
    return _post("/v1/new/endpoint", {"param": param})
```

> Методы `_post` автоматически retry при `Timeout`/`ConnectionError` (3 попытки, exponential backoff).

---

## 📊 Локальная LLM (Ollama)

По умолчанию в `docker-compose.yml` поднимается контейнер Ollama. Для использования локальной модели вместо GigaChat:

```bash
# Подключись к контейнеру Ollama и скачай модель
docker exec -it ozon_ollama ollama pull qwen2.5:7b
```

В коде используй `LocalLLM` из `ai/local.py`.

Для GPU добавь в `docker-compose.yml` (раскомментируй блок `deploy` в сервисе `ollama`).

---

## 🐛 Устранение неполадок

### Бот не подключается к Telegram (Россия)

```bash
# Проверь, что api.telegram.org доступен
curl -I https://api.telegram.org

# Если нет — включи прокси в .env:
USE_BOT_PROXY=true
BOT_PROXY_LIST=http://user:pass@proxy:port

# Тест прокси:
curl -x http://user:pass@proxy:port https://api.telegram.org/bot<token>/getMe
```

### Бот падает с ошибкой "empty result from Ozon API"

Проверь:
1. `API_TOKEN` и `CLIENT_ID` корректны
2. У бота на Ozon есть права на управление отзывами

### `uv sync` медленный

```bash
UV_LINK_MODE=copy uv sync   # если hardlink не работает на твоей FS
```

### Docker: прокси на хосте

Если прокси крутится на Docker-хосте, раскомментируй в `docker-compose.yml`:
```yaml
extra_hosts:
  - "proxy.local:host-gateway"
```

---

## 📁 Управление зависимостями

Проект использует **uv** — быстрый менеджер Python-зависимостей.

| Задача | Команда |
|--------|---------|
| Установка | `uv sync` |
| Запуск | `uv run main.py` |
| Добавить пакет | `uv add <name>` |
| Удалить пакет | `uv remove <name>` |
| Обновить lock | `uv lock` |
| Dev-зависимости | `uv sync --dev` |
| Линтинг | `uv run --dev ruff check .` |
| Форматирование | `uv run --dev ruff format .` |

---

## 📚 Полезные ссылки

- [aiogram FSM документация](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Ozon Seller API](https://docs.ozon.ru/api/seller/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [uv документация](https://docs.astral.sh/uv/)