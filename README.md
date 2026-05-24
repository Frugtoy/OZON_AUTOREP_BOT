# Ozon AutoReply Bot

Автоматический ответчик на отзывы Ozon через Telegram-бота.

## Запуск

### Docker
```bash
docker build . -t my_bot_app
```

### Локально
```bash
bash ./launch.sh
```

## Конфигурация

Скопируйте `.env-example` в `.env` и заполните:

### Обязательные переменные
- `API_TOKEN` — токен Ozon API
- `CLIENT_ID` — ID клиента Ozon
- `GIGACHAT_CREDENTIALS` — ключ GigaChat
- `BOT_TOKEN` — токен Telegram-бота

### Прокси (для Telegram из России)

- `USE_BOT_PROXY=true` — включить прокси для Telegram
- `BOT_PROXY_LIST=http://user:pass@host:port` — список прокси через запятую

### Пример .env с прокси
```env
API_TOKEN=your_api_token
CLIENT_ID=your_client_id
GIGACHAT_CREDENTIALS=your_gigachat_key
BOT_TOKEN=your_bot_token

USE_BOT_PROXY=true
BOT_PROXY_LIST=http://user:pass@proxy1:8080
```

---

## Архитектура проекта

```
ozon_autorep_bot/
├── config/          # Конфигурация (pydantic-settings, логи)
├── db/              # SQLite: ReviewManager
├── api/             # Ozon API клиент
├── ai/              # LLM: GigaChat + Local (Ollama)
├── bot/             # Telegram handlers (aiogram)
├── services/        # Бизнес-логика
├── main.py          # Точка входа
└── fileworker.py    # JSON-конфиги (rating_1..5, score_list, admin_list)
```

### Поток данных
1. **Ozon API** → `api/ozon.py` → `db/manager.py` (SQLite)
2. **Telegram** → `bot/handlers.py` → `services/review_service.py` → Ozon API + DB
3. **AI генерация** → `ai/` → Ozon API (ответы на отзывы)

---

## Как добавить новый сценарий (кнопка → ввод)

Все сценарии бота построены по одной схеме: **inline-кнопка → FSM-состояние → обработка ввода → выход из состояния**.

### Пошаговая инструкция

#### 1. Добавить состояние в FSM

В `bot/handlers.py` (или отдельном `bot/states.py`):

```python
class Form(StatesGroup):
    # ... существующие состояния ...
    MY_NEW_FEATURE = State()  # ← новое состояние
```

#### 2. Добавить кнопку в меню

Найди место, куда нужна кнопка (например, главное меню или подменю конфига):

```python
# Внутри нужного callback handler или команды
kb = InlineKeyboardBuilder()
kb.button(text="Моя новая фича", callback_data="my_new_feature")
kb.adjust(1)
await callback.message.edit_text("Выберите действие:", reply_markup=kb.as_markup())
```

#### 3. Обработать нажатие кнопки (callback)

```python
@router.callback_query(F.data == "my_new_feature")
async def my_feature_start(callback: CallbackQuery, state: FSMContext):
    # Проверка прав (опционально)
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("Нужны права администратора.")
        return
    
    # Переводим пользователя в состояние ожидания ввода
    await state.set_state(Form.MY_NEW_FEATURE)
    await callback.message.edit_text("Введите данные:")
```

#### 4. Обработать ввод пользователя

```python
@router.message(Form.MY_NEW_FEATURE)
async def process_my_feature(message: Message, state: FSMContext):
    user_input = message.text.strip()
    
    # Валидация
    if not user_input:
        await message.answer("Ввод не может быть пустым. Попробуйте ещё раз:")
        return
    
    # Бизнес-логика
    # Например: сохранить в БД, отправить в API, записать в JSON
    data = get_all_reviews()  # или ReviewManager()
    data["my_new_field"] = user_input
    save_reviews(data)
    
    # Выход из состояния
    await state.clear()
    await message.answer(f"✅ Сохранено: {user_input}")
```

#### 5. (Опционально) Добавить inline-выбор вместо текстового ввода

Если нужен выбор из вариантов, а не свободный ввод:

```python
@router.callback_query(F.data == "my_new_feature")
async def my_feature_menu(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="Вариант 1", callback_data="my_feature_1")
    kb.button(text="Вариант 2", callback_data="my_feature_2")
    kb.button(text="↩️ Назад", callback_data="config_setup")
    kb.adjust(1)
    await callback.message.edit_text("Выберите вариант:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("my_feature_"))
async def process_feature_choice(callback: CallbackQuery):
    choice = callback.data.split("_")[-1]
    # ... обработка ...
    await callback.message.edit_text(f"Выбрано: {choice}")
```

---

### Примеры существующих сценариев

| Сценарий | Файл | Кнопка | Состояние | Что вводится |
|----------|------|--------|-----------|--------------|
| Добавить админа | `bot/handlers.py` | `add_admin` | `Form.ADMIN_ADD_USER` | `chat_id` (число) |
| Удалить админа | `bot/handlers.py` | `remove_admin` | `Form.ADMIN_REMOVE_USER` | `chat_id` (число) |
| Добавить отзыв | `bot/handlers.py` | `add_review` → `add_review_rating_{N}` | `Form.ADD_REVIEW_TEXT` | Текст отзыва |
| Фильтр рейтинга | `bot/handlers.py` | `add_rating` | `Form.FILTER_RATING_ACTION` | Число 1–5 |

---

## Добавление нового модуля AI

Если нужен не GigaChat/Ollama, а другой провайдер:

1. Создай файл `ai/new_provider.py`:
```python
class NewProvider:
    async def generate(self, rating: int, review_text: str, category=None) -> str:
        # ... реализация ...
        return "Ответ"
```

2. Экспортируй из `ai/__init__.py`:
```python
from .new_provider import NewProvider
__all__ = ["GigaChatGenerator", "LocalLLM", "NewProvider"]
```

3. Используй в `services/review_service.py` или `bot/handlers.py`.

---

## Расширение Ozon API

В `api/ozon.py` добавь метод:

```python
def new_ozon_method(param: str) -> Dict[str, Any]:
    return _post("/v1/new/endpoint", {"param": param})
```

И экспортируй из `api/__init__.py`.

---

## Полезные ссылки

- [aiogram FSM документация](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Ozon Seller API](https://docs.ozon.ru/api/seller/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
