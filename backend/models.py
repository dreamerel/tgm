from datetime import datetime
import json

# Вместо базы данных используем in-memory хранилище
# Для MVP будем хранить данные в словарях

# Хранилище пользователей
users = {}
# {id: {'id': int, 'username': str, 'password_hash': str, 'email': str}}

# Хранилище токенов для сессий
tokens = {}
# {token: user_id}

# Хранилище аккаунтов Telegram
telegram_accounts = {}
# {id: {'id': int, 'user_id': int, 'account_name': str, 'phone': str}}

# Хранилище контактов
contacts = {}
# {id: {'id': int, 'account_id': int, 'name': str, 'phone': str}}

# Хранилище чатов
chats = {}
# {id: {'id': int, 'account_id': int, 'contact_id': int, 'last_message': str, 'unread_count': int}}

# Хранилище сообщений
messages = {}
# {id: {'id': int, 'chat_id': int, 'sender_id': int, 'text': str, 'timestamp': datetime, 'is_read': bool}}

# Хранилище авто-ответов
auto_replies = {}
# {id: {'id': int, 'account_id': int, 'trigger_phrase': str, 'reply_text': str, 'is_active': bool}}

# Хранилище массовых рассылок
mass_sendings = {}
# {id: {'id': int, 'account_id': int, 'message': str, 'contacts': list, 'delay': int, 'frequency': int, 'status': str, 'sent_count': int}}

# Хранилище статистики
statistics = {}
# {id: {'id': int, 'account_id': int, 'date': datetime, 'sent_messages': int, 'received_messages': int}}


# Функции для работы с хранилищем

def save_user(username, password_hash, email=None):
    """Сохранить нового пользователя"""
    user_id = len(users) + 1
    users[user_id] = {
        'id': user_id,
        'username': username,
        'password_hash': password_hash,
        'email': email
    }
    return user_id


def get_user_by_username(username):
    """Получить пользователя по имени"""
    for user_id, user in users.items():
        if user['username'] == username:
            return user
    return None


def get_user_by_id(user_id):
    """Получить пользователя по ID"""
    return users.get(user_id)


def save_telegram_account(user_id, account_name, phone):
    """Сохранить аккаунт Telegram"""
    account_id = len(telegram_accounts) + 1
    telegram_accounts[account_id] = {
        'id': account_id,
        'user_id': user_id,
        'account_name': account_name,
        'phone': phone
    }
    return account_id


def get_telegram_accounts(user_id):
    """Получить все аккаунты Telegram пользователя"""
    return [account for account_id, account in telegram_accounts.items() 
            if account['user_id'] == user_id]


def save_contact(account_id, name, phone):
    """Сохранить контакт"""
    contact_id = len(contacts) + 1
    contacts[contact_id] = {
        'id': contact_id,
        'account_id': account_id,
        'name': name,
        'phone': phone
    }
    return contact_id


def get_contacts(account_id):
    """Получить контакты аккаунта"""
    return [contact for contact_id, contact in contacts.items() 
            if contact['account_id'] == account_id]


def save_chat(account_id, contact_id, last_message='', unread_count=0):
    """Сохранить чат"""
    chat_id = len(chats) + 1
    chats[chat_id] = {
        'id': chat_id,
        'account_id': account_id,
        'contact_id': contact_id,
        'last_message': last_message,
        'unread_count': unread_count
    }
    return chat_id


def get_chats(account_id):
    """Получить чаты аккаунта"""
    return [chat for chat_id, chat in chats.items() 
            if chat['account_id'] == account_id]


def save_message(chat_id, sender_id, text):
    """Сохранить сообщение"""
    message_id = len(messages) + 1
    timestamp = datetime.now()
    messages[message_id] = {
        'id': message_id,
        'chat_id': chat_id,
        'sender_id': sender_id,
        'text': text,
        'timestamp': timestamp,
        'is_read': False
    }
    # Обновляем последнее сообщение в чате
    for chat_id_key, chat in chats.items():
        if chat_id_key == chat_id:
            chat['last_message'] = text
            if sender_id != 0:  # Если отправитель не пользователь
                chat['unread_count'] += 1
    return message_id


def get_messages(chat_id):
    """Получить сообщения чата"""
    chat_messages = [message for message_id, message in messages.items() 
                    if message['chat_id'] == chat_id]
    # Сортируем по времени
    chat_messages.sort(key=lambda x: x['timestamp'])
    return chat_messages


def save_auto_reply(account_id, trigger_phrase, reply_text, is_active=True):
    """Сохранить авто-ответ"""
    auto_reply_id = len(auto_replies) + 1
    auto_replies[auto_reply_id] = {
        'id': auto_reply_id,
        'account_id': account_id,
        'trigger_phrase': trigger_phrase,
        'reply_text': reply_text,
        'is_active': is_active
    }
    return auto_reply_id


def get_auto_replies(account_id):
    """Получить авто-ответы аккаунта"""
    return [auto_reply for auto_reply_id, auto_reply in auto_replies.items() 
            if auto_reply['account_id'] == account_id]


def save_mass_sending(account_id, message, contacts_list, delay, frequency):
    """Сохранить массовую рассылку"""
    mass_sending_id = len(mass_sendings) + 1
    mass_sendings[mass_sending_id] = {
        'id': mass_sending_id,
        'account_id': account_id,
        'message': message,
        'contacts': contacts_list,
        'delay': delay,
        'frequency': frequency,
        'status': 'pending',
        'sent_count': 0
    }
    return mass_sending_id


def get_mass_sendings(account_id):
    """Получить массовые рассылки аккаунта"""
    return [sending for sending_id, sending in mass_sendings.items() 
            if sending['account_id'] == account_id]


def update_statistics(account_id, sent=0, received=0):
    """Обновить статистику"""
    today = datetime.now().date()
    today_str = today.isoformat()
    
    # Ищем запись за сегодня
    for stat_id, stat in statistics.items():
        if stat['account_id'] == account_id and stat['date'].date().isoformat() == today_str:
            stat['sent_messages'] += sent
            stat['received_messages'] += received
            return stat_id
    
    # Если запись за сегодня не найдена, создаем новую
    stat_id = len(statistics) + 1
    statistics[stat_id] = {
        'id': stat_id,
        'account_id': account_id,
        'date': today,
        'sent_messages': sent,
        'received_messages': received
    }
    return stat_id


def get_statistics(account_id, days=7):
    """Получить статистику аккаунта за указанное количество дней"""
    account_stats = [stat for stat_id, stat in statistics.items() 
                    if stat['account_id'] == account_id]
    # Сортируем по дате
    account_stats.sort(key=lambda x: x['date'], reverse=True)
    # Возвращаем статистику за указанное количество дней
    return account_stats[:days]


# Инициализация данных для демонстрации
def init_demo_data():
    """Инициализация демонстрационных данных"""
    from werkzeug.security import generate_password_hash
    
    # Создаем тестового пользователя
    user_id = save_user('demo', generate_password_hash('demo123'), 'demo@example.com')
    
    # Создаем тестовые аккаунты Telegram
    account1_id = save_telegram_account(user_id, 'Личный', '+79123456789')
    account2_id = save_telegram_account(user_id, 'Рабочий', '+79987654321')
    
    # Создаем тестовые контакты
    contact1_id = save_contact(account1_id, 'Иван Иванов', '+79001112233')
    contact2_id = save_contact(account1_id, 'Мария Петрова', '+79004445566')
    contact3_id = save_contact(account2_id, 'ООО "Компания"', '+79007778899')
    
    # Создаем тестовые чаты
    chat1_id = save_chat(account1_id, contact1_id)
    chat2_id = save_chat(account1_id, contact2_id)
    chat3_id = save_chat(account2_id, contact3_id)
    
    # Добавляем тестовые сообщения
    save_message(chat1_id, contact1_id, 'Привет, как дела?')
    save_message(chat1_id, user_id, 'Привет! Все хорошо, спасибо!')
    save_message(chat2_id, contact2_id, 'Добрый день, когда встречаемся?')
    save_message(chat3_id, contact3_id, 'Добрый день, отправляю коммерческое предложение.')
    
    # Создаем тестовые авто-ответы
    save_auto_reply(account1_id, 'привет', 'Привет! Чем могу помочь?')
    save_auto_reply(account2_id, 'цена', 'Актуальные цены можно узнать на нашем сайте.')
    
    # Создаем тестовую массовую рассылку
    save_mass_sending(account1_id, 'Привет! Приглашаю на мероприятие!', [contact1_id, contact2_id], 60, 2)
    
    # Инициализируем статистику
    update_statistics(account1_id, 10, 15)
    update_statistics(account2_id, 5, 3)


# Инициализация демо-данных при запуске
init_demo_data()
