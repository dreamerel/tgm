from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from backend.models import get_user_by_id, get_telegram_accounts

def jwt_required_custom(fn):
    """Декоратор для проверки JWT токена"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            
            # Проверяем, что identity существует и может быть преобразован в int
            current_user_id = get_jwt_identity()
            user_id = int(current_user_id)
            
            # Проверяем, что пользователь существует в системе
            user = get_user_by_id(user_id)
            if not user:
                return jsonify({"error": "Пользователь не найден"}), 404
                
            return fn(*args, **kwargs)
        except ValueError:
            return jsonify({"error": "Неверный формат идентификатора пользователя"}), 422
        except Exception as e:
            return jsonify({"error": f"Ошибка авторизации: {str(e)}"}), 401
    return wrapper

def account_owner_required(fn):
    """Декоратор для проверки владельца аккаунта Telegram"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Преобразуем ID пользователя из строки в int
            user_id = int(current_user_id)
            
            # Получаем ID аккаунта из параметров запроса
            account_id = request.args.get('account_id')
            if not account_id:
                account_id = request.json.get('account_id')
            
            if not account_id:
                return jsonify({"error": "Требуется указать ID аккаунта"}), 400
            
            # Получаем список аккаунтов пользователя
            user_accounts = get_telegram_accounts(user_id)
            
            # Проверяем, принадлежит ли аккаунт пользователю
            if not any(account['id'] == int(account_id) for account in user_accounts):
                return jsonify({"error": "У вас нет доступа к этому аккаунту"}), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Ошибка авторизации: {str(e)}"}), 401
    return wrapper

def validate_user_input(schema):
    """Декоратор для валидации входных данных"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.json
            
            errors = {}
            for field, rules in schema.items():
                # Проверяем обязательность поля
                if 'required' in rules and rules['required'] and (field not in data or data[field] is None):
                    errors[field] = 'Это поле обязательно'
                    continue
                
                # Если поле отсутствует и не обязательно, пропускаем проверки
                if field not in data or data[field] is None:
                    continue
                
                # Проверяем тип
                if 'type' in rules:
                    if rules['type'] == 'string' and not isinstance(data[field], str):
                        errors[field] = 'Значение должно быть строкой'
                    elif rules['type'] == 'integer' and not isinstance(data[field], int):
                        errors[field] = 'Значение должно быть целым числом'
                    elif rules['type'] == 'array' and not isinstance(data[field], list):
                        errors[field] = 'Значение должно быть массивом'
                
                # Проверяем минимальную длину строки
                if 'min_length' in rules and isinstance(data[field], str) and len(data[field]) < rules['min_length']:
                    errors[field] = f'Минимальная длина: {rules["min_length"]} символов'
                
                # Проверяем максимальную длину строки
                if 'max_length' in rules and isinstance(data[field], str) and len(data[field]) > rules['max_length']:
                    errors[field] = f'Максимальная длина: {rules["max_length"]} символов'
            
            if errors:
                return jsonify({"errors": errors}), 400
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
