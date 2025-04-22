from datetime import datetime
import json
import os
import time

# Путь к файлу для хранения данных
DATABASE_FILE = 'telegram_manager_data.json'

# Структура для хранения данных в памяти
data = {
    'users': {},
    'telegram_accounts': {},
    'contacts': {},
    'chats': {},
    'messages': {},
    'auto_replies': {},
    'mass_sendings': {},
    'statistics': {}
}

# Загружаем данные из файла, если он существует
def load_data():
    global data
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                data = loaded_data
                print(f"Данные успешно загружены из {DATABASE_FILE}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Ошибка при загрузке данных: {e}")
            # В случае ошибки инициализируем пустые данные
            data = {
                'users': {},
                'telegram_accounts': {},
                'contacts': {},
                'chats': {},
                'messages': {},
                'auto_replies': {},
                'mass_sendings': {},
                'statistics': {}
            }
    else:
        print(f"Файл {DATABASE_FILE} не найден. Будет создан новый файл.")


# Сохраняем данные в файл
def save_data():
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Данные успешно сохранены в {DATABASE_FILE}")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")


# Загружаем данные при запуске
load_data()

# Вспомогательные функции для работы с данными
def get_next_id(entity_type):
    """Получить следующий ID для указанного типа сущности"""
    if not data[entity_type]:
        return 1
    ids = [int(id) for id in data[entity_type].keys()]
    return max(ids) + 1 if ids else 1


def datetime_to_str(dt):
    """Преобразовать datetime в строку для сохранения в JSON"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt


def str_to_datetime(dt_str):
    """Преобразовать строку в datetime при загрузке из JSON"""
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return dt_str


# Функции для работы с данными

def save_user(username, password_hash, email=None):
    """Сохранить нового пользователя"""
    # Проверяем, существует ли уже пользователь с таким именем
    for user_id, user in data['users'].items():
        if user['username'] == username:
            return int(user_id)  # Возвращаем существующий ID

    user_id = get_next_id('users')
    data['users'][str(user_id)] = {
        'id': user_id,
        'username': username,
        'password_hash': password_hash,
        'email': email,
        'created_at': datetime_to_str(datetime.utcnow())
    }
    save_data()  # Сохраняем изменения в файл
    return user_id


def get_user_by_username(username):
    """Получить пользователя по имени"""
    for user_id, user in data['users'].items():
        if user['username'] == username:
            return user
    return None


def get_user_by_id(user_id):
    """Получить пользователя по ID"""
    return data['users'].get(str(user_id))


def save_telegram_account(user_id, account_name, phone):
    """Сохранить аккаунт Telegram"""
    account_id = get_next_id('telegram_accounts')
    data['telegram_accounts'][str(account_id)] = {
        'id': account_id,
        'user_id': user_id,
        'account_name': account_name,
        'phone': phone,
        'created_at': datetime_to_str(datetime.utcnow())
    }
    save_data()  # Сохраняем изменения в файл
    return account_id


def get_telegram_accounts(user_id):
    """Получить все аккаунты Telegram пользователя"""
    return [account for account_id, account in data['telegram_accounts'].items() 
            if account['user_id'] == user_id]


def save_contact(account_id, name, phone):
    """Сохранить контакт"""
    contact_id = get_next_id('contacts')
    data['contacts'][str(contact_id)] = {
        'id': contact_id,
        'account_id': account_id,
        'name': name,
        'phone': phone,
        'created_at': datetime_to_str(datetime.utcnow())
    }
    save_data()  # Сохраняем изменения в файл
    return contact_id


def get_contacts(account_id):
    """Получить контакты аккаунта"""
    return [contact for contact_id, contact in data['contacts'].items() 
            if contact['account_id'] == account_id]


def save_chat(account_id, contact_id, last_message='', unread_count=0):
    """Сохранить чат"""
    chat_id = get_next_id('chats')
    data['chats'][str(chat_id)] = {
        'id': chat_id,
        'account_id': account_id,
        'contact_id': contact_id,
        'last_message': last_message,
        'unread_count': unread_count,
        'created_at': datetime_to_str(datetime.utcnow())
    }
    save_data()  # Сохраняем изменения в файл
    return chat_id


def get_chats(account_id):
    """Получить чаты аккаунта"""
    return [chat for chat_id, chat in data['chats'].items() 
            if chat['account_id'] == account_id]


def save_message(chat_id, sender_id, text):
    """Сохранить сообщение"""
    message_id = get_next_id('messages')
    timestamp = datetime.utcnow()
    data['messages'][str(message_id)] = {
        'id': message_id,
        'chat_id': chat_id,
        'sender_id': sender_id,
        'text': text,
        'timestamp': datetime_to_str(timestamp),
        'is_read': False
    }
    
    # Обновляем последнее сообщение в чате
    for chat_id_key, chat in data['chats'].items():
        if int(chat_id_key) == chat_id:
            chat['last_message'] = text
            if sender_id != 0:  # Если отправитель не пользователь
                chat['unread_count'] += 1
    
    save_data()  # Сохраняем изменения в файл
    return message_id


def get_messages(chat_id):
    """Получить сообщения чата"""
    chat_messages = [message for message_id, message in data['messages'].items() 
                    if message['chat_id'] == chat_id]
    # Сортируем по времени
    chat_messages.sort(key=lambda x: x['timestamp'])
    return chat_messages


def save_auto_reply(account_id, trigger_phrase, reply_text, is_active=True):
    """Сохранить авто-ответ"""
    auto_reply_id = get_next_id('auto_replies')
    data['auto_replies'][str(auto_reply_id)] = {
        'id': auto_reply_id,
        'account_id': account_id,
        'trigger_phrase': trigger_phrase,
        'reply_text': reply_text,
        'is_active': is_active,
        'created_at': datetime_to_str(datetime.utcnow())
    }
    save_data()  # Сохраняем изменения в файл
    return auto_reply_id


def get_auto_replies(account_id):
    """Получить авто-ответы аккаунта"""
    return [auto_reply for auto_reply_id, auto_reply in data['auto_replies'].items() 
            if auto_reply['account_id'] == account_id]


def save_mass_sending(account_id, message, contacts_list, delay, frequency):
    """Сохранить массовую рассылку"""
    mass_sending_id = get_next_id('mass_sendings')
    data['mass_sendings'][str(mass_sending_id)] = {
        'id': mass_sending_id,
        'account_id': account_id,
        'message': message,
        'contacts': contacts_list,
        'delay': delay,
        'frequency': frequency,
        'status': 'pending',
        'sent_count': 0,
        'created_at': datetime_to_str(datetime.utcnow())
    }
    save_data()  # Сохраняем изменения в файл
    return mass_sending_id


def get_mass_sendings(account_id):
    """Получить массовые рассылки аккаунта"""
    return [sending for sending_id, sending in data['mass_sendings'].items() 
            if sending['account_id'] == account_id]


def update_statistics(account_id, sent=0, received=0):
    """Обновить статистику"""
    today = datetime.now().date().isoformat()
    
    # Ищем запись за сегодня
    for stat_id, stat in data['statistics'].items():
        if stat['account_id'] == account_id and stat['date'] == today:
            stat['sent_messages'] += sent
            stat['received_messages'] += received
            save_data()  # Сохраняем изменения в файл
            return int(stat_id)
    
    # Если запись за сегодня не найдена, создаем новую
    stat_id = get_next_id('statistics')
    data['statistics'][str(stat_id)] = {
        'id': stat_id,
        'account_id': account_id,
        'date': today,
        'sent_messages': sent,
        'received_messages': received
    }
    save_data()  # Сохраняем изменения в файл
    return stat_id


def get_statistics(account_id, days=7):
    """Получить статистику аккаунта за указанное количество дней"""
    account_stats = [stat for stat_id, stat in data['statistics'].items() 
                    if stat['account_id'] == account_id]
    # Сортируем по дате
    account_stats.sort(key=lambda x: x['date'], reverse=True)
    # Возвращаем статистику за указанное количество дней
    return account_stats[:days]


# Инициализация данных для демонстрации
def init_demo_data():
    """Инициализация демонстрационных данных"""
    from werkzeug.security import generate_password_hash
    
    # Проверяем наличие демо-пользователя
    demo_user = get_user_by_username('demo')
    if not demo_user:
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
        save_message(chat1_id, 0, 'Привет! Все хорошо, спасибо!')
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
