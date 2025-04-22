import os
import logging
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Настройка JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
jwt = JWTManager(app)

# Включение CORS для разработки
CORS(app, resources={r"/*": {"origins": "*"}})

# Импорт маршрутов после создания приложения
from routes import *
