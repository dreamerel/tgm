from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import time

from backend.app import app
from backend.models import (
    get_user_by_username, get_user_by_id, save_user,
    get_telegram_accounts, save_telegram_account,
    get_contacts, save_contact, get_chats, save_chat,
    get_messages, save_message, get_auto_replies, save_auto_reply,
    get_mass_sendings, save_mass_sending, get_statistics, update_statistics
)
from backend.telegram_mock import simulate_telegram_api_call


@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email') or None  # Если email пустой, устанавливаем None
    
    if not username or not password:
        return jsonify({'error': 'Требуется указать имя пользователя и пароль'}), 400
    
    if get_user_by_username(username):
        return jsonify({'error': 'Пользователь с таким именем уже существует'}), 409
    
    # Если email предоставлен, проверим его уникальность
    if email:
        # Проверка на существование пользователя с таким email
        # В текущей реализации такой функции нет, но она может быть добавлена позже
        # if get_user_by_email(email):
        #     return jsonify({'error': 'Пользователь с таким email уже существует'}), 409
        pass
    
    # Хэшируем пароль и сохраняем пользователя
    password_hash = generate_password_hash(password)
    user_id = save_user(username, password_hash, email)
    
    # Возвращаем токены для аутентификации
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    
    return jsonify({
        'message': 'Пользователь успешно зарегистрирован',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user_id,
            'username': username,
            'email': email
        }
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Вход пользователя"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Требуется указать имя пользователя и пароль'}), 400
    
    user = get_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401
    
    # Возвращаем токены для аутентификации
    access_token = create_access_token(identity=user['id'])
    refresh_token = create_refresh_token(identity=user['id'])
    
    return jsonify({
        'message': 'Успешный вход',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    }), 200


@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Обновление access токена"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200


@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    """Получение информации о текущем пользователе"""
    current_user_id = get_jwt_identity()
    user = get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    }), 200


@app.route('/api/telegram/accounts', methods=['GET'])
@jwt_required()
def list_telegram_accounts():
    """Список аккаунтов Telegram пользователя"""
    current_user_id = get_jwt_identity()
    accounts = get_telegram_accounts(current_user_id)
    
    return jsonify({'accounts': accounts}), 200


@app.route('/api/telegram/accounts', methods=['POST'])
@jwt_required()
def add_telegram_account():
    """Добавление нового аккаунта Telegram"""
    current_user_id = get_jwt_identity()
    data = request.json
    
    account_name = data.get('account_name')
    phone = data.get('phone')
    
    if not account_name or not phone:
        return jsonify({'error': 'Требуется указать название аккаунта и номер телефона'}), 400
    
    # Проверяем возможность добавления аккаунта через мок API Telegram
    result = simulate_telegram_api_call('add_account', {'phone': phone})
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    account_id = save_telegram_account(current_user_id, account_name, phone)
    
    return jsonify({
        'message': 'Аккаунт Telegram успешно добавлен',
        'account': {
            'id': account_id,
            'account_name': account_name,
            'phone': phone
        }
    }), 201


@app.route('/api/telegram/contacts', methods=['GET'])
@jwt_required()
def list_contacts():
    """Список контактов аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    contacts_list = get_contacts(account_id)
    
    return jsonify({'contacts': contacts_list}), 200


@app.route('/api/telegram/contacts', methods=['POST'])
@jwt_required()
def add_contact():
    """Добавление нового контакта"""
    data = request.json
    
    account_id = data.get('account_id')
    name = data.get('name')
    phone = data.get('phone')
    
    if not account_id or not name or not phone:
        return jsonify({'error': 'Требуется указать ID аккаунта, имя и номер телефона'}), 400
    
    # Проверяем возможность добавления контакта через мок API Telegram
    result = simulate_telegram_api_call('add_contact', {'phone': phone, 'name': name})
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    contact_id = save_contact(account_id, name, phone)
    
    return jsonify({
        'message': 'Контакт успешно добавлен',
        'contact': {
            'id': contact_id,
            'account_id': account_id,
            'name': name,
            'phone': phone
        }
    }), 201


@app.route('/api/telegram/contacts/import', methods=['POST'])
@jwt_required()
def import_contacts():
    """Импорт контактов"""
    data = request.json
    
    account_id = data.get('account_id')
    contacts_data = data.get('contacts', [])
    
    if not account_id or not contacts_data:
        return jsonify({'error': 'Требуется указать ID аккаунта и список контактов'}), 400
    
    imported_contacts = []
    for contact in contacts_data:
        name = contact.get('name')
        phone = contact.get('phone')
        
        if name and phone:
            # Мок запрос к API
            result = simulate_telegram_api_call('add_contact', {'phone': phone, 'name': name})
            
            if 'error' not in result:
                contact_id = save_contact(account_id, name, phone)
                imported_contacts.append({
                    'id': contact_id,
                    'name': name,
                    'phone': phone
                })
    
    return jsonify({
        'message': f'Успешно импортировано {len(imported_contacts)} контактов',
        'contacts': imported_contacts
    }), 200


@app.route('/api/telegram/chats', methods=['GET'])
@jwt_required()
def list_chats():
    """Список чатов аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    chats_list = get_chats(account_id)
    
    # Добавляем информацию о контакте в каждый чат
    for chat in chats_list:
        contact_id = chat['contact_id']
        contact = next((c for c in get_contacts(account_id) if c['id'] == contact_id), None)
        if contact:
            chat['contact'] = contact
    
    return jsonify({'chats': chats_list}), 200


@app.route('/api/telegram/messages', methods=['GET'])
@jwt_required()
def list_messages():
    """Список сообщений чата"""
    chat_id = request.args.get('chat_id', type=int)
    
    if not chat_id:
        return jsonify({'error': 'Требуется указать ID чата'}), 400
    
    messages_list = get_messages(chat_id)
    
    return jsonify({'messages': messages_list}), 200


@app.route('/api/telegram/messages', methods=['POST'])
@jwt_required()
def send_message():
    """Отправка сообщения"""
    data = request.json
    
    chat_id = data.get('chat_id')
    message_text = data.get('text')
    
    if not chat_id or not message_text:
        return jsonify({'error': 'Требуется указать ID чата и текст сообщения'}), 400
    
    # Получаем информацию о чате
    chat = None
    for chat_key, chat_value in get_chats(None):
        if chat_key == chat_id:
            chat = chat_value
            break
    
    if not chat:
        return jsonify({'error': 'Чат не найден'}), 404
    
    # Мок запрос к API для отправки сообщения
    result = simulate_telegram_api_call('send_message', {
        'chat_id': chat_id,
        'text': message_text
    })
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    # Сохраняем сообщение как отправленное пользователем (sender_id=0)
    current_user_id = get_jwt_identity()
    message_id = save_message(chat_id, current_user_id, message_text)
    
    # Обновляем статистику
    update_statistics(chat['account_id'], sent=1)
    
    # Проверяем на авто-ответ
    auto_replies_list = get_auto_replies(chat['account_id'])
    for auto_reply in auto_replies_list:
        if auto_reply['is_active'] and auto_reply['trigger_phrase'].lower() in message_text.lower():
            # Задержка для имитации ответа от Telegram
            time.sleep(1)
            
            # Сохраняем авто-ответ как сообщение от контакта
            reply_id = save_message(chat_id, chat['contact_id'], auto_reply['reply_text'])
            
            # Обновляем статистику
            update_statistics(chat['account_id'], received=1)
            
            break
    
    return jsonify({
        'message': 'Сообщение успешно отправлено',
        'message_id': message_id
    }), 201


@app.route('/api/telegram/auto-replies', methods=['GET'])
@jwt_required()
def list_auto_replies():
    """Список авто-ответов аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    auto_replies_list = get_auto_replies(account_id)
    
    return jsonify({'auto_replies': auto_replies_list}), 200


@app.route('/api/telegram/auto-replies', methods=['POST'])
@jwt_required()
def add_auto_reply():
    """Добавление нового авто-ответа"""
    data = request.json
    
    account_id = data.get('account_id')
    trigger_phrase = data.get('trigger_phrase')
    reply_text = data.get('reply_text')
    is_active = data.get('is_active', True)
    
    if not account_id or not trigger_phrase or not reply_text:
        return jsonify({'error': 'Требуется указать ID аккаунта, фразу-триггер и текст ответа'}), 400
    
    auto_reply_id = save_auto_reply(account_id, trigger_phrase, reply_text, is_active)
    
    return jsonify({
        'message': 'Авто-ответ успешно добавлен',
        'auto_reply': {
            'id': auto_reply_id,
            'account_id': account_id,
            'trigger_phrase': trigger_phrase,
            'reply_text': reply_text,
            'is_active': is_active
        }
    }), 201


@app.route('/api/telegram/auto-replies/<int:auto_reply_id>', methods=['PUT'])
@jwt_required()
def update_auto_reply(auto_reply_id):
    """Обновление авто-ответа"""
    data = request.json
    
    trigger_phrase = data.get('trigger_phrase')
    reply_text = data.get('reply_text')
    is_active = data.get('is_active')
    
    # В реальном приложении здесь был бы код для обновления в БД
    # Сейчас просто имитируем успешное обновление
    
    return jsonify({
        'message': 'Авто-ответ успешно обновлен',
        'auto_reply': {
            'id': auto_reply_id,
            'trigger_phrase': trigger_phrase,
            'reply_text': reply_text,
            'is_active': is_active
        }
    }), 200


@app.route('/api/telegram/mass-sendings', methods=['GET'])
@jwt_required()
def list_mass_sendings():
    """Список массовых рассылок аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    mass_sendings_list = get_mass_sendings(account_id)
    
    return jsonify({'mass_sendings': mass_sendings_list}), 200


@app.route('/api/telegram/mass-sendings', methods=['POST'])
@jwt_required()
def add_mass_sending():
    """Добавление новой массовой рассылки"""
    data = request.json
    
    account_id = data.get('account_id')
    message = data.get('message')
    contacts_list = data.get('contacts')
    delay = data.get('delay', 60)  # задержка между сообщениями в секундах
    frequency = data.get('frequency', 5)  # количество сообщений в минуту
    
    if not account_id or not message or not contacts_list:
        return jsonify({'error': 'Требуется указать ID аккаунта, сообщение и список контактов'}), 400
    
    # Мок запрос к API для проверки возможности рассылки
    result = simulate_telegram_api_call('check_mass_sending', {
        'account_id': account_id,
        'contacts_count': len(contacts_list)
    })
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    mass_sending_id = save_mass_sending(account_id, message, contacts_list, delay, frequency)
    
    # В реальном приложении здесь бы запускался фоновый процесс для рассылки
    # В MVP будем просто возвращать информацию о созданной рассылке
    
    return jsonify({
        'message': 'Массовая рассылка успешно создана',
        'mass_sending': {
            'id': mass_sending_id,
            'account_id': account_id,
            'message': message,
            'contacts_count': len(contacts_list),
            'delay': delay,
            'frequency': frequency,
            'status': 'pending'
        }
    }), 201


@app.route('/api/telegram/statistics', methods=['GET'])
@jwt_required()
def get_account_statistics():
    """Получение статистики аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    stats = get_statistics(account_id, days)
    
    return jsonify({'statistics': stats}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({'status': 'ok'}), 200


# Маршруты для React-приложения
from backend.app import frontend_build_path
from flask import send_from_directory

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """
    Обслуживает React-приложение.
    Все пути, кроме /api/*, направляются на соответствующие HTML файлы
    """
    if path.startswith('api/'):
        return jsonify({"error": "Not Found"}), 404
    
    # Проверяем известные маршруты
    if path == 'register':
        return send_from_directory(str(frontend_build_path), 'register.html')
    
    if path.startswith('dashboard'):
        return send_from_directory(str(frontend_build_path), 'dashboard/index.html')
        
    # Проверяем, существует ли запрашиваемый файл
    if path and (frontend_build_path / path).exists():
        return send_from_directory(str(frontend_build_path), path)
    
    # В противном случае возвращаем index.html для поддержки маршрутизации на стороне клиента
    return send_from_directory(str(frontend_build_path), 'index.html')
