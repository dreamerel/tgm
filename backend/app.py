import os
import logging
from datetime import timedelta
from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Определение пути к собранным файлам React
frontend_build_path = Path(__file__).resolve().parent.parent / 'frontend' / 'build'

# Создание приложения Flask
app = Flask(__name__, static_folder=str(frontend_build_path / 'static'))
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Настройка JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
jwt = JWTManager(app)

# Включение CORS с расширенной конфигурацией для обработки preflight-запросов
# Если задан CORS_ORIGIN в переменных окружения, используем его
# Иначе разрешаем все возможные источники, включая Vercel и localhost
cors_origins = os.environ.get('CORS_ORIGIN', 'https://tgm-tau.vercel.app,http://localhost:3000,*').split(',')
logging.debug(f"CORS origins: {cors_origins}")

CORS(app, 
     resources={r"/*": {"origins": cors_origins}}, 
     supports_credentials=True, 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
     expose_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
     max_age=86400,
     vary_header=True)
