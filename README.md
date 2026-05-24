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
