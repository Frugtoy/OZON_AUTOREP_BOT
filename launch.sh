#!/bin/bash

VOLUME_NAME="my_bot_data"
IMAGE_NAME="my_bot_app"
CONTAINER_NAME="my_bot_container"

# Проверяем существование тома
if ! docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
    echo "Том '$VOLUME_NAME' не найден. Создаём..."
    docker volume create "$VOLUME_NAME"
else
    echo "Том '$VOLUME_NAME' уже существует."
fi

# Запускаем контейнер
echo "Запускаем контейнер..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -v "$VOLUME_NAME":/app/data \
    "$IMAGE_NAME"

echo "Контейнер успешно запущен!"