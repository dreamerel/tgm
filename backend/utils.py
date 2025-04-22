import re
import random
import string
from datetime import datetime

def validate_phone(phone):
    """Проверка корректности формата телефонного номера"""
    # Простая проверка: должен начинаться с + и содержать от 10 до 15 цифр
    pattern = r'^\+[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def validate_email(email):
    """Проверка корректности формата email"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def generate_random_string(length=10):
    """Генерация случайной строки заданной длины"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def format_datetime(dt):
    """Форматирование даты и времени для отображения"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    
    now = datetime.now()
    
    # Если сегодня
    if dt.date() == now.date():
        return dt.strftime('%H:%M')
    
    # Если вчера
    yesterday = (now.date() - timedelta(days=1))
    if dt.date() == yesterday:
        return f'Вчера, {dt.strftime("%H:%M")}'
    
    # Если в этом году
    if dt.year == now.year:
        return dt.strftime('%d %b, %H:%M')
    
    # Если в другом году
    return dt.strftime('%d.%m.%Y, %H:%M')

def split_message_by_length(message, max_length=4096):
    """Разделение сообщения на части по максимальной длине"""
    if len(message) <= max_length:
        return [message]
    
    parts = []
    for i in range(0, len(message), max_length):
        parts.append(message[i:i+max_length])
    
    return parts

def parse_html_entities(text):
    """Обработка HTML-сущностей в тексте"""
    entities = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'"
    }
    
    for entity, char in entities.items():
        text = text.replace(entity, char)
    
    return text

def escape_html(text):
    """Экранирование HTML-символов в тексте"""
    entities = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#39;'
    }
    
    for char, entity in entities.items():
        text = text.replace(char, entity)
    
    return text
