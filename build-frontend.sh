#!/bin/bash

echo "Сборка фронтенда..."
cd frontend
npm install
npm run build

# Копируем собранные файлы в директорию backend/static
echo "Копирование собранных файлов..."
mkdir -p ../backend/static
cp -r build/* ../backend/static/

echo "Сборка фронтенда завершена."