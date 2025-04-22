import sys
import os

# Добавляем текущий каталог в путь поиска модулей
sys.path.insert(0, os.path.abspath('.'))

# Импортируем приложение из backend/app.py
from backend.app import app
# Импортируем остальные модули
import backend.models
import backend.routes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)