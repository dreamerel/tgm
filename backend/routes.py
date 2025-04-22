from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import time

from backend.app import app
from backend.auth import jwt_required_custom, account_owner_required, jwt_refresh_token_required
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


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Вход пользователя"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Требуется указать имя пользователя и пароль'}), 400
    
    # Специальная обработка для демо-аккаунта
    if username == 'demo' and password == 'demo123':
        # Получаем пользователя или создаем его, если он отсутствует
        user = get_user_by_username('demo')
        if not user:
            # Если демо-пользователь не существует, инициализируем данные
            from backend.models import init_demo_data
            init_demo_data()
            user = get_user_by_username('demo')
    else:
        user = get_user_by_username(username)
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401
    
    # Возвращаем токены для аутентификации
    access_token = create_access_token(identity=str(user['id']))
    refresh_token = create_refresh_token(identity=str(user['id']))
    
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


@app.route('/api/auth/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    """Обновление access токена"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        return jsonify({'access_token': access_token}), 200
    except Exception as e:
        # Логирование ошибки
        app.logger.error(f"Ошибка при обновлении токена: {str(e)}")
        return jsonify({'error': 'Не удалось обновить токен'}), 401


@app.route('/api/user', methods=['GET'])
@jwt_required_custom
def get_user():
    """Получение информации о текущем пользователе"""
    try:
        current_user_id = get_jwt_identity()
        # Преобразуем ID из строки в int
        user_id = int(current_user_id)
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    except Exception as e:
        # Логирование ошибки
        app.logger.error(f"Ошибка при получении данных пользователя: {str(e)}")
        return jsonify({'error': 'Не удалось получить данные пользователя'}), 400


@app.route('/api/telegram/accounts', methods=['GET'])
@jwt_required_custom
def list_telegram_accounts():
    """Список аккаунтов Telegram пользователя"""
    try:
        current_user_id = get_jwt_identity()
        # Преобразуем ID из строки в int
        user_id = int(current_user_id)
        accounts = get_telegram_accounts(user_id)
        
        return jsonify({'accounts': accounts}), 200
    except Exception as e:
        # Логирование ошибки
        app.logger.error(f"Ошибка при получении списка аккаунтов: {str(e)}")
        return jsonify({'error': 'Не удалось получить список аккаунтов Telegram', 'accounts': []}), 200
        
        
@app.route('/api/telegram/accounts/send-code', methods=['POST'])
@jwt_required_custom
def send_telegram_code():
    """Отправка кода подтверждения для авторизации в Telegram"""
    from backend.telegram_api import run_async, send_code_request
    
    data = request.json
    phone = data.get('phone')
    api_id = data.get('api_id')
    api_hash = data.get('api_hash')
    
    app.logger.info(f"Получен запрос на отправку кода подтверждения: телефон={phone}, api_id={api_id}")
    
    if not phone or not api_id or not api_hash:
        app.logger.error(f"Отсутствуют обязательные параметры для отправки кода")
        return jsonify({'error': 'Необходимо указать номер телефона, API ID и API Hash'}), 400
    
    try:
        api_id = int(api_id)
    except ValueError:
        app.logger.error(f"Некорректный формат API ID: {api_id}")
        return jsonify({'error': 'API ID должен быть числом'}), 400
    
    # Проверяем, есть ли уже сохраненная сессия для этого аккаунта
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['phone'] == phone), None)
    
    if account and account.get('session_string'):
        app.logger.info(f"Аккаунт {phone} уже имеет сохраненную сессию, пропускаем отправку кода")
        return jsonify({
            'success': True,
            'message': 'Аккаунт уже авторизован с использованием сохраненной сессии',
            'phone_code_hash': '',
            'authorized': True
        }), 200
    
    # Отправляем запрос на код подтверждения
    app.logger.info(f"Отправляем запрос на получение кода для {phone} с API ID {api_id}")
    result = run_async(send_code_request(phone, api_id, api_hash))
    app.logger.info(f"Результат запроса кода для {phone}: {result}")
    
    if 'error' in result:
        app.logger.error(f"Ошибка при отправке кода для {phone}: {result['error']}")
        return jsonify({'error': result['error']}), 400
    
    return jsonify({
        'success': True,
        'message': result.get('message', 'Код подтверждения отправлен'),
        'phone_code_hash': result.get('phone_code_hash', ''),
        'authorized': result.get('authorized', False)
    }), 200
        
        
@app.route('/api/telegram/accounts/verify-code', methods=['POST'])
@jwt_required_custom
def verify_telegram_code():
    """Верификация кода подтверждения для авторизации в Telegram"""
    from backend.telegram_api import run_async, sign_in_with_code
    
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    phone_code_hash = data.get('phone_code_hash')
    api_id = data.get('api_id')
    api_hash = data.get('api_hash')
    password = data.get('password')  # Пароль 2FA (если требуется)
    
    if not phone or not code or not phone_code_hash or not api_id or not api_hash:
        return jsonify({'error': 'Не все необходимые параметры предоставлены'}), 400
    
    try:
        api_id = int(api_id)
    except ValueError:
        return jsonify({'error': 'API ID должен быть числом'}), 400
    
    # Проверяем код и входим в аккаунт
    result = run_async(sign_in_with_code(phone, code, phone_code_hash, api_id, api_hash, password))
    
    if 'error' in result:
        # Если требуется 2FA и пароль не был предоставлен
        if result.get('two_factor_required', False):
            return jsonify({
                'error': result['error'],
                'two_factor_required': True
            }), 401  # Unauthorized, требуется дополнительная аутентификация
            
        return jsonify({'error': result['error']}), 400
    
    # Обновляем статус аккаунта в базе данных
    # Находим аккаунт по номеру телефона
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    accounts = get_telegram_accounts(user_id)
    
    session_string = result.get('session_string')
    account_id = None
    
    for account in accounts:
        if account['phone'] == phone:
            account_id = account['id']
            # Обновляем данные аккаунта с сохранением строки сессии
            from backend.models import update_telegram_account
            update_telegram_account(account_id, 
                status='authorized', 
                session_string=session_string
            )
            app.logger.info(f"Аккаунт {phone} успешно авторизован и сохранена строка сессии")
            break
    
    if not account_id:
        app.logger.error(f"Не найден аккаунт с номером {phone} для пользователя {user_id}")
        return jsonify({'error': 'Аккаунт не найден'}), 404
            
    return jsonify({
        'success': True,
        'message': 'Авторизация успешно завершена',
        'session_saved': bool(session_string),
        'user_info': result.get('user_info', {})
    }), 200


@app.route('/api/telegram/accounts', methods=['POST'])
@jwt_required_custom
def add_telegram_account():
    """Добавление нового аккаунта Telegram с использованием Telethon"""
    from backend.telegram_api import run_async, create_telegram_client
    
    current_user_id = get_jwt_identity()
    # Преобразуем ID из строки в int
    user_id = int(current_user_id)
    data = request.json
    
    account_name = data.get('account_name')
    phone = data.get('phone')
    api_id = data.get('api_id')
    api_hash = data.get('api_hash')
    
    if not account_name or not phone:
        return jsonify({'error': 'Требуется указать название аккаунта и номер телефона'}), 400
    
    # Проверяем API ID и API Hash, если они предоставлены
    if (api_id and not api_hash) or (not api_id and api_hash):
        return jsonify({'error': 'Необходимо указать оба параметра: API ID и API Hash'}), 400
    
    # Проверяем валидность API ID, если он предоставлен
    if api_id:
        try:
            api_id = int(api_id)
        except ValueError:
            return jsonify({'error': 'API ID должен быть числом'}), 400
    
    # Если API ID и API Hash не предоставлены, возвращаем ошибку
    if not api_id or not api_hash:
        return jsonify({
            'error': 'Необходимо указать API ID и API Hash для работы с Telegram. Получите их на https://my.telegram.org/apps'
        }), 400
    
    # Если API ID и API Hash предоставлены, пытаемся подключиться через Telethon
    result = run_async(create_telegram_client(phone, api_id, api_hash))
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    # Получаем строку сессии, если есть
    session_string = result.get('session_string')
    
    # Сохраняем аккаунт в базе данных
    account_id = save_telegram_account(
        user_id, 
        account_name, 
        phone, 
        api_id, 
        api_hash, 
        session_string=session_string
    )
    
    # Информация об авторизации
    status = 'authorized' if result.get('authorized', False) else 'pending'
    user_info = result.get('user_info', {})
    
    message = 'Аккаунт Telegram успешно добавлен'
    if status == 'pending':
        message += '. Для завершения авторизации требуется код подтверждения'
    elif status == 'authorized' and session_string:
        message += ' и авторизован с сохранением сессии'
    
    response = {
        'message': message,
        'account': {
            'id': account_id,
            'account_name': account_name,
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'status': status,
            'session_saved': bool(session_string)
        }
    }
    
    # Если аккаунт авторизован, добавляем информацию о пользователе
    if status == 'authorized' and user_info:
        response['account']['user_info'] = user_info
    
    return jsonify(response), 201


@app.route('/api/telegram/contacts', methods=['GET'])
@jwt_required_custom
def list_contacts():
    """Список контактов аккаунта Telegram"""
    from backend.telegram_api import run_async, get_contacts as tg_get_contacts, create_telegram_client
    
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    # Получаем аккаунт по ID
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({'error': 'Аккаунт не найден'}), 404
    
    # Если у аккаунта есть API ID и API Hash, получаем контакты через Telegram API
    if account.get('api_id') and account.get('api_hash'):
        # Если у аккаунта сохранена строка сессии, пытаемся использовать ее сначала
        session_string = account.get('session_string')
        
        # Если сессия есть, пробуем подключиться с ее использованием
        if session_string:
            app.logger.info(f"Подключаемся к аккаунту {account['phone']} с использованием сохраненной сессии")
            # Создаем клиент с использованием строки сессии
            client_result = run_async(
                create_telegram_client(
                    account['phone'], 
                    account['api_id'], 
                    account['api_hash'], 
                    session_string=session_string
                )
            )
            
            # Если успешно подключились и авторизованы, получаем контакты
            if client_result.get('success') and client_result.get('authorized'):
                app.logger.info(f"Успешно подключились к аккаунту {account['phone']} с использованием сессии")
                # Получаем контакты
                result = run_async(tg_get_contacts(account['phone']))
            else:
                app.logger.warning(f"Не удалось использовать сохраненную сессию для {account['phone']}: {client_result.get('error', 'неизвестная ошибка')}")
                # Если не удалось подключиться с сессией, пытаемся получить контакты обычным способом
                result = run_async(tg_get_contacts(account['phone']))
        else:
            # Если нет сохраненной сессии, просто пытаемся получить контакты
            result = run_async(tg_get_contacts(account['phone']))
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Обновляем контакты в нашей базе данных
        contacts_from_tg = result.get('contacts', [])
        saved_contacts = []
        
        for contact in contacts_from_tg:
            name = contact.get('first_name', '')
            if contact.get('last_name'):
                name += f" {contact.get('last_name')}"
            
            saved_contact_id = save_contact(
                account_id, 
                name or "Контакт без имени", 
                contact.get('phone', '') or ""
            )
            
            saved_contacts.append({
                'id': saved_contact_id,
                'name': name or "Контакт без имени",
                'phone': contact.get('phone', '') or "",
                'username': contact.get('username', ''),
                'telegram_id': contact.get('id')
            })
        
        return jsonify({'contacts': saved_contacts}), 200
    
    # Если API ID и API Hash не указаны, возвращаем ошибку
    return jsonify({'error': 'Для получения контактов необходимо указать API ID и API Hash для аккаунта'}), 400


@app.route('/api/telegram/contacts', methods=['POST'])
@jwt_required_custom
def add_contact():
    """Добавление нового контакта через Telegram API"""
    data = request.json
    
    account_id = data.get('account_id')
    name = data.get('name')
    phone = data.get('phone')
    
    if not account_id or not name or not phone:
        return jsonify({'error': 'Требуется указать ID аккаунта, имя и номер телефона'}), 400
    
    # Получаем аккаунт по ID
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({'error': 'Аккаунт не найден'}), 404
    
    # Если у аккаунта есть API ID и API Hash
    if account.get('api_id') and account.get('api_hash'):
        # TODO: Реализовать добавление контакта через Telegram API
        # Для этого нужно добавить соответствующий метод в telegram_api.py
        # В данной версии просто сохраняем контакт в базе данных
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
    
    # Если API ID и API Hash не указаны, возвращаем ошибку
    return jsonify({'error': 'Для добавления контакта необходимо указать API ID и API Hash для аккаунта'}), 400


@app.route('/api/telegram/contacts/import', methods=['POST'])
@jwt_required_custom
def import_contacts():
    """Импорт контактов"""
    data = request.json
    
    account_id = data.get('account_id')
    contacts_data = data.get('contacts', [])
    
    if not account_id or not contacts_data:
        return jsonify({'error': 'Требуется указать ID аккаунта и список контактов'}), 400
    
    # Получаем аккаунт по ID
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({'error': 'Аккаунт не найден'}), 404
    
    # Если у аккаунта есть API ID и API Hash
    if account.get('api_id') and account.get('api_hash'):
        imported_contacts = []
        for contact in contacts_data:
            name = contact.get('name')
            phone = contact.get('phone')
            
            if name and phone:
                # TODO: В будущем добавить метод для реального добавления контакта через Telegram API
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
    
    # Если API ID и API Hash не указаны, возвращаем ошибку
    return jsonify({'error': 'Для импорта контактов необходимо указать API ID и API Hash для аккаунта'}), 400


@app.route('/api/telegram/chats', methods=['GET'])
@jwt_required_custom
def list_chats():
    """Список чатов аккаунта Telegram"""
    from backend.telegram_api import run_async, get_dialogs, create_telegram_client
    
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    # Получаем аккаунт по ID
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({'error': 'Аккаунт не найден'}), 404
    
    # Если у аккаунта есть API ID и API Hash, получаем чаты через Telegram API
    if account.get('api_id') and account.get('api_hash'):
        # Если у аккаунта сохранена строка сессии, пытаемся использовать ее сначала
        session_string = account.get('session_string')
        
        # Если сессия есть, пробуем подключиться с ее использованием
        if session_string:
            app.logger.info(f"Подключаемся к аккаунту {account['phone']} с использованием сохраненной сессии")
            # Создаем клиент с использованием строки сессии
            client_result = run_async(
                create_telegram_client(
                    account['phone'], 
                    account['api_id'], 
                    account['api_hash'], 
                    session_string=session_string
                )
            )
            
            # Если успешно подключились и авторизованы, получаем чаты
            if client_result.get('success') and client_result.get('authorized'):
                app.logger.info(f"Успешно подключились к аккаунту {account['phone']} с использованием сессии")
                # Получаем чаты
                result = run_async(get_dialogs(account['phone']))
            else:
                app.logger.warning(f"Не удалось использовать сохраненную сессию для {account['phone']}: {client_result.get('error', 'неизвестная ошибка')}")
                # Если не удалось подключиться с сессией, пытаемся получить чаты обычным способом
                result = run_async(get_dialogs(account['phone']))
        else:
            # Если нет сохраненной сессии, просто пытаемся получить чаты
            result = run_async(get_dialogs(account['phone']))
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Преобразуем диалоги в формат чатов для нашего приложения
        dialogs_from_tg = result.get('dialogs', [])
        saved_chats = []
        
        for dialog in dialogs_from_tg:
            # Сначала добавляем или находим контакт
            name = dialog.get('name', '')
            
            contact_id = None
            contacts = get_contacts(account_id)
            
            # Ищем контакт по entity_id (Telegram ID)
            contact = next((c for c in contacts if c.get('telegram_id') == dialog.get('entity_id')), None)
            
            if contact:
                contact_id = contact['id']
            else:
                # Создаем новый контакт
                contact_id = save_contact(
                    account_id, 
                    name or "Неизвестный контакт", 
                    ""  # Телефон неизвестен
                )
            
            # Сохраняем чат
            chat_id = None
            chats = get_chats(account_id)
            
            # Ищем существующий чат по Telegram ID
            chat = next((c for c in chats if c.get('telegram_id') == dialog.get('id')), None)
            
            if chat:
                chat_id = chat['id']
                # Обновляем информацию в чате
                # В текущей модели на основе JSON это требует отдельной реализации
            else:
                # Создаем новый чат
                last_message = ""
                if dialog.get('last_message') and dialog.get('last_message').get('text'):
                    last_message = dialog.get('last_message').get('text')
                
                chat_id = save_chat(
                    account_id, 
                    contact_id, 
                    last_message,
                    dialog.get('unread_count', 0)
                )
            
            saved_chat = {
                'id': chat_id,
                'account_id': account_id,
                'contact_id': contact_id,
                'telegram_id': dialog.get('id'),
                'telegram_entity_id': dialog.get('entity_id'),
                'name': name,
                'last_message': dialog.get('last_message', {}).get('text', ''),
                'unread_count': dialog.get('unread_count', 0),
                'contact': {
                    'id': contact_id,
                    'name': name
                }
            }
            
            saved_chats.append(saved_chat)
        
        return jsonify({'chats': saved_chats}), 200
    
    # Если API ID и API Hash не указаны, возвращаем существующие чаты из нашей базы данных
    chats_list = get_chats(account_id)
    
    # Добавляем информацию о контакте в каждый чат
    for chat in chats_list:
        contact_id = chat['contact_id']
        contact = next((c for c in get_contacts(account_id) if c['id'] == contact_id), None)
        if contact:
            chat['contact'] = contact
    
    return jsonify({'chats': chats_list}), 200


@app.route('/api/telegram/messages', methods=['GET'])
@jwt_required_custom
def list_messages():
    """Список сообщений чата"""
    from backend.telegram_api import run_async, get_messages as tg_get_messages
    
    chat_id = request.args.get('chat_id', type=int)
    
    if not chat_id:
        return jsonify({'error': 'Требуется указать ID чата'}), 400
    
    # Находим чат по ID
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id)
    
    # Собираем все чаты из всех аккаунтов пользователя
    all_chats = []
    for account in get_telegram_accounts(user_id):
        all_chats.extend(get_chats(account['id']))
    
    chat = next((c for c in all_chats if c['id'] == chat_id), None)
    
    if not chat:
        return jsonify({'error': 'Чат не найден'}), 404
    
    account_id = chat['account_id']
    
    # Получаем аккаунт по ID
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({'error': 'Аккаунт не найден'}), 404
    
    # Если у аккаунта есть API ID и API Hash и в чате есть Telegram ID сущности
    if account.get('api_id') and account.get('api_hash') and chat.get('telegram_entity_id'):
        # Если у аккаунта сохранена строка сессии, пытаемся использовать ее сначала
        session_string = account.get('session_string')
        
        # Если сессия есть, пробуем подключиться с ее использованием
        if session_string:
            app.logger.info(f"Подключаемся к аккаунту {account['phone']} с использованием сохраненной сессии для получения сообщений")
            # Создаем клиент с использованием строки сессии
            client_result = run_async(
                create_telegram_client(
                    account['phone'], 
                    account['api_id'], 
                    account['api_hash'], 
                    session_string=session_string
                )
            )
            
            # Если успешно подключились и авторизованы, получаем сообщения
            if client_result.get('success') and client_result.get('authorized'):
                app.logger.info(f"Успешно подключились к аккаунту {account['phone']} с использованием сессии")
                # Получаем сообщения
                result = run_async(tg_get_messages(account['phone'], chat['telegram_entity_id']))
            else:
                app.logger.warning(f"Не удалось использовать сохраненную сессию для {account['phone']}: {client_result.get('error', 'неизвестная ошибка')}")
                # Если не удалось подключиться с сессией, пытаемся получить сообщения обычным способом
                result = run_async(tg_get_messages(account['phone'], chat['telegram_entity_id']))
        else:
            # Если нет сохраненной сессии, просто пытаемся получить сообщения
            result = run_async(tg_get_messages(account['phone'], chat['telegram_entity_id']))
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Преобразуем сообщения в формат для нашего приложения
        messages_from_tg = result.get('messages', [])
        saved_messages = []
        
        for msg in messages_from_tg:
            # Определяем отправителя сообщения
            sender_id = chat['contact_id']  # По умолчанию, сообщение от контакта
            if msg.get('out', False):
                sender_id = user_id  # Если сообщение исходящее, отправитель - текущий пользователь
            
            # Сохраняем сообщение в нашей базе данных
            # В реальном приложении нужно избегать дублирования сообщений
            message_id = save_message(
                chat_id,
                sender_id,
                msg.get('text', '')
            )
            
            saved_messages.append({
                'id': message_id,
                'chat_id': chat_id,
                'sender_id': sender_id,
                'text': msg.get('text', ''),
                'date': msg.get('date'),
                'telegram_id': msg.get('id')
            })
        
        return jsonify({'messages': saved_messages}), 200
    
    # Если API ID и API Hash не указаны или нет Telegram entity ID, возвращаем сообщения из локальной базы
    messages_list = get_messages(chat_id)
    
    return jsonify({'messages': messages_list}), 200


@app.route('/api/telegram/messages', methods=['POST'])
@jwt_required_custom
def send_message():
    """Отправка сообщения через Telegram API"""
    from backend.telegram_api import run_async, send_message_to_contact
    
    data = request.json
    
    chat_id = data.get('chat_id')
    message_text = data.get('text')
    
    if not chat_id or not message_text:
        return jsonify({'error': 'Требуется указать ID чата и текст сообщения'}), 400
    
    # Получаем информацию о чате
    chats_list = []
    current_user_id = get_jwt_identity()
    # Преобразуем ID из строки в int
    user_id = int(current_user_id)
    for account in get_telegram_accounts(user_id):
        chats_list.extend(get_chats(account['id']))
    
    chat = next((chat for chat in chats_list if chat['id'] == chat_id), None)
    
    if not chat:
        return jsonify({'error': 'Чат не найден'}), 404
    
    account_id = chat['account_id']
    
    # Получаем аккаунт по ID
    accounts = get_telegram_accounts(user_id)
    account = next((acc for acc in accounts if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({'error': 'Аккаунт не найден'}), 404
    
    # Если у аккаунта есть API ID и API Hash и в чате есть Telegram ID сущности
    if account.get('api_id') and account.get('api_hash') and chat.get('telegram_entity_id'):
        entity_id = chat['telegram_entity_id']
        result = run_async(send_message_to_contact(account['phone'], entity_id, message_text))
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Сохраняем сообщение как отправленное пользователем
        message_id = save_message(chat_id, user_id, message_text)
        
        # Обновляем статистику
        update_statistics(account_id, sent=1)
        
        return jsonify({
            'message': 'Сообщение успешно отправлено',
            'message_id': message_id,
            'telegram_message_id': result.get('message_id'),
            'date': result.get('date')
        }), 201
    
    # Если API ID и API Hash не указаны или нет Telegram entity ID
    # Сохраняем сообщение как отправленное пользователем (в локальной базе)
    message_id = save_message(chat_id, user_id, message_text)
    
    # Обновляем статистику
    update_statistics(chat['account_id'], sent=1)
    
    # Проверяем на авто-ответ (для демо-режима)
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
        'message': 'Сообщение успешно отправлено (в локальном режиме)',
        'message_id': message_id
    }), 201


@app.route('/api/telegram/auto-replies', methods=['GET'])
@jwt_required_custom
def list_auto_replies():
    """Список авто-ответов аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    auto_replies_list = get_auto_replies(account_id)
    
    return jsonify({'auto_replies': auto_replies_list}), 200


@app.route('/api/telegram/auto-replies', methods=['POST'])
@jwt_required_custom
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
@jwt_required_custom
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
@jwt_required_custom
def list_mass_sendings():
    """Список массовых рассылок аккаунта Telegram"""
    account_id = request.args.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'Требуется указать ID аккаунта'}), 400
    
    mass_sendings_list = get_mass_sendings(account_id)
    
    return jsonify({'mass_sendings': mass_sendings_list}), 200


@app.route('/api/telegram/mass-sendings', methods=['POST'])
@jwt_required_custom
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
@jwt_required_custom
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

# Добавим обработчик OPTIONS для CORS preflight-запросов
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Обработка preflight запросов CORS"""
    response = app.response_class(
        status=204
    )
    
    # Получаем список разрешенных источников
    allowed_origins = app.config.get('CORS_ORIGINS', ['*'])
    
    # Получаем источник запроса из заголовка
    origin = request.headers.get('Origin', '*')
    
    # Если источник в списке разрешенных или разрешены все источники ('*' в списке)
    if origin in allowed_origins or '*' in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', allowed_origins[0] if allowed_origins else '*')
    
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Access-Control-Allow-Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')  # 24 часа
    return response


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
