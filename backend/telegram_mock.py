import random
import time
from datetime import datetime

# Моки для имитации взаимодействия с API Telegram
# В реальном приложении здесь был бы код для работы с Telethon

def simulate_telegram_api_call(method, params):
    """
    Имитация вызова API Telegram
    
    method: Метод API
    params: Параметры запроса
    """
    # Имитация задержки сети
    time.sleep(0.5)
    
    # Случайный сбой для демонстрации обработки ошибок
    if random.random() < 0.05:  # 5% шанс ошибки
        return {
            'error': 'Ошибка соединения с Telegram API. Попробуйте позже.'
        }
    
    # Обработка разных методов API
    if method == 'add_account':
        # Проверка формата телефона (примитивная)
        phone = params.get('phone', '')
        if not phone.startswith('+') or len(phone) < 10:
            return {
                'error': 'Неверный формат номера телефона. Используйте формат +XXXXXXXXXXX'
            }
        
        # Успешный ответ
        return {
            'success': True,
            'account': {
                'phone': phone,
                'created_at': datetime.now().isoformat()
            }
        }
    
    elif method == 'add_contact':
        # Проверка данных контакта
        phone = params.get('phone', '')
        name = params.get('name', '')
        
        if not phone or not name:
            return {
                'error': 'Необходимо указать номер телефона и имя контакта'
            }
        
        # Успешный ответ
        return {
            'success': True,
            'contact': {
                'phone': phone,
                'name': name,
                'created_at': datetime.now().isoformat()
            }
        }
    
    elif method == 'send_message':
        # Проверка данных сообщения
        chat_id = params.get('chat_id')
        text = params.get('text', '')
        
        if not chat_id or not text:
            return {
                'error': 'Необходимо указать ID чата и текст сообщения'
            }
        
        # Успешный ответ
        return {
            'success': True,
            'message': {
                'chat_id': chat_id,
                'text': text,
                'sent_at': datetime.now().isoformat()
            }
        }
    
    elif method == 'check_mass_sending':
        # Проверка параметров рассылки
        account_id = params.get('account_id')
        contacts_count = params.get('contacts_count', 0)
        
        if not account_id:
            return {
                'error': 'Необходимо указать ID аккаунта'
            }
        
        if contacts_count > 100:
            return {
                'error': 'Превышен лимит контактов для массовой рассылки (максимум 100)'
            }
        
        # Успешный ответ
        return {
            'success': True,
            'limits': {
                'max_contacts': 100,
                'max_frequency': 10,  # сообщений в минуту
                'daily_limit': 500
            }
        }
    
    # Метод не распознан
    return {
        'error': f'Неизвестный метод API: {method}'
    }


def simulate_incoming_message(chat_id, sender_name, message_text):
    """
    Имитация входящего сообщения от пользователя Telegram
    В реальном приложении это был бы обработчик событий от Telethon
    
    chat_id: ID чата
    sender_name: Имя отправителя
    message_text: Текст сообщения
    """
    # В реальном приложении здесь был бы код для добавления сообщения в БД
    # и уведомления подключенных клиентов через веб-сокеты
    
    return {
        'chat_id': chat_id,
        'sender_name': sender_name,
        'text': message_text,
        'received_at': datetime.now().isoformat()
    }
