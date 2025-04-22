import os
import logging
import asyncio
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneNumberInvalidError, 
    ApiIdInvalidError, 
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    FloodWaitError
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Каталог для хранения сессий Telegram
SESSIONS_DIR = Path('telegram_sessions')
SESSIONS_DIR.mkdir(exist_ok=True)

# Кэш клиентов Telegram для разных аккаунтов
clients = {}

async def create_telegram_client(phone, api_id, api_hash, session_string=None, session_name=None):
    """
    Создает и возвращает клиент Telegram
    
    phone: Номер телефона аккаунта
    api_id: API ID из my.telegram.org
    api_hash: API Hash из my.telegram.org
    session_string: Строка сессии (опционально)
    session_name: Имя файла сессии (по умолчанию - номер телефона)
    """
    # Проверяем, есть ли строка сессии
    if session_string:
        # Создаем клиент с использованием строки сессии
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        logger.info(f"Создан клиент для {phone} из строки сессии")
    else:
        # Стандартное создание клиента с файловой сессией
        if not session_name:
            # Удаляем все нецифровые символы из номера телефона для имени сессии
            session_name = ''.join(filter(str.isdigit, phone))
        
        session_path = SESSIONS_DIR / session_name
        
        # Создаем клиент
        client = TelegramClient(str(session_path), api_id, api_hash)
        logger.info(f"Создан клиент для {phone} с файловой сессией")
    
    try:
        # Пытаемся подключиться
        await client.connect()
        
        # Если уже авторизован, возвращаем клиент
        if await client.is_user_authorized():
            logger.info(f"Успешно подключен к аккаунту {phone}")
            # Сохраняем клиент в кэше
            clients[phone] = client
            
            # Получаем информацию о пользователе
            me = await client.get_me()
            
            # Создаем строку сессии для сохранения (если еще не было)
            if not session_string:
                session_string = StringSession.save(client.session)
            
            return {
                'success': True, 
                'authorized': True,
                'session_string': session_string,
                'user_info': {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'username': me.username,
                    'phone': me.phone
                }
            }
        else:
            # Если не авторизован, возвращаем информацию для дальнейшей авторизации
            logger.info(f"Требуется авторизация для аккаунта {phone}")
            
            # Не отправляем код здесь, это будет отдельный шаг
            return {
                'success': True,
                'authorized': False,
                'message': 'Для завершения авторизации требуется код подтверждения'
            }
    
    except PhoneNumberInvalidError:
        await client.disconnect()
        return {'error': 'Неверный формат номера телефона'}
    
    except ApiIdInvalidError:
        await client.disconnect()
        return {'error': 'Неверный API ID или API Hash'}
    
    except Exception as e:
        logger.error(f"Ошибка при создании клиента Telegram: {str(e)}")
        await client.disconnect()
        return {'error': f'Ошибка соединения с Telegram: {str(e)}'}

async def send_code_request(phone, api_id, api_hash):
    """
    Отправляет запрос на получение кода подтверждения
    
    phone: Номер телефона аккаунта
    api_id: API ID из my.telegram.org
    api_hash: API Hash из my.telegram.org
    """
    session_name = ''.join(filter(str.isdigit, phone))
    session_path = SESSIONS_DIR / session_name
    
    # Создаем клиент
    client = TelegramClient(str(session_path), api_id, api_hash)
    
    try:
        # Подключаемся
        await client.connect()
        
        # Если уже авторизован, возвращаем успех
        if await client.is_user_authorized():
            return {
                'success': True,
                'message': 'Аккаунт уже авторизован',
                'authorized': True
            }
        
        # Отправляем запрос на код
        sent = await client.send_code_request(phone)
        
        # Сохраняем информацию о типе отправки (SMS, звонок и т.д.)
        return {
            'success': True,
            'phone_code_hash': sent.phone_code_hash,
            'message': 'Код подтверждения отправлен',
            'authorized': False
        }
    
    except PhoneNumberInvalidError:
        await client.disconnect()
        return {'error': 'Неверный формат номера телефона'}
    
    except ApiIdInvalidError:
        await client.disconnect()
        return {'error': 'Неверный API ID или API Hash'}
    
    except Exception as e:
        logger.error(f"Ошибка при отправке кода: {str(e)}")
        await client.disconnect()
        return {'error': f'Ошибка при отправке кода: {str(e)}'}

async def sign_in_with_code(phone, code, phone_code_hash, api_id, api_hash, password=None):
    """
    Выполняет вход в аккаунт с использованием кода подтверждения
    
    phone: Номер телефона аккаунта
    code: Код подтверждения, полученный по SMS или через Telegram
    phone_code_hash: Хеш, полученный при запросе кода
    api_id: API ID из my.telegram.org
    api_hash: API Hash из my.telegram.org
    password: Пароль двухфакторной аутентификации (если требуется)
    """
    session_name = ''.join(filter(str.isdigit, phone))
    session_path = SESSIONS_DIR / session_name
    
    # Создаем клиент
    client = TelegramClient(str(session_path), api_id, api_hash)
    
    try:
        # Подключаемся
        await client.connect()
        
        # Если уже авторизован, возвращаем успех
        if await client.is_user_authorized():
            clients[phone] = client
            
            # Получаем информацию о пользователе
            me = await client.get_me()
            
            # Создаем строку сессии для сохранения
            session_string = StringSession.save(client.session)
            
            return {
                'success': True, 
                'authorized': True,
                'session_string': session_string,
                'user_info': {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'username': me.username,
                    'phone': me.phone
                }
            }
        
        try:
            # Пытаемся войти с кодом
            user = await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Сохраняем клиент в кэше
            clients[phone] = client
            
            # Создаем строку сессии для сохранения
            session_string = StringSession.save(client.session)
            
            return {
                'success': True,
                'authorized': True,
                'session_string': session_string,
                'user_info': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'phone': user.phone
                }
            }
            
        except PhoneCodeInvalidError:
            return {'error': 'Неверный код подтверждения'}
            
        except SessionPasswordNeededError:
            # Если требуется пароль 2FA
            if password:
                # Пытаемся войти с паролем
                user = await client.sign_in(password=password)
                
                # Сохраняем клиент в кэше
                clients[phone] = client
                
                # Создаем строку сессии для сохранения
                session_string = StringSession.save(client.session)
                
                return {
                    'success': True,
                    'authorized': True,
                    'session_string': session_string,
                    'user_info': {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'phone': user.phone
                    }
                }
            else:
                return {
                    'error': 'Требуется пароль двухфакторной аутентификации',
                    'two_factor_required': True
                }
    
    except Exception as e:
        logger.error(f"Ошибка при входе с кодом: {str(e)}")
        await client.disconnect()
        return {'error': f'Ошибка при входе: {str(e)}'}

async def get_contacts(phone):
    """
    Получает список контактов из Telegram
    
    phone: Номер телефона аккаунта
    """
    if phone not in clients:
        return {'error': 'Аккаунт не авторизован'}
    
    client = clients[phone]
    
    try:
        contacts = []
        async for contact in client.iter_contacts():
            contacts.append({
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'username': contact.username,
                'phone': contact.phone
            })
        
        return {
            'success': True,
            'contacts': contacts
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении контактов: {str(e)}")
        return {'error': f'Ошибка при получении контактов: {str(e)}'}

async def get_dialogs(phone, limit=100):
    """
    Получает список диалогов (чатов) из Telegram
    
    phone: Номер телефона аккаунта
    limit: Максимальное количество диалогов для получения
    """
    if phone not in clients:
        return {'error': 'Аккаунт не авторизован'}
    
    client = clients[phone]
    
    try:
        dialogs = []
        async for dialog in client.iter_dialogs(limit=limit):
            # Проверяем, является ли диалог чатом с пользователем (не группой, не каналом)
            if dialog.is_user:
                entity = dialog.entity
                
                # Формируем информацию о диалоге
                dialog_info = {
                    'id': dialog.id,
                    'name': '',
                    'entity_id': entity.id,
                    'username': getattr(entity, 'username', None),
                    'unread_count': dialog.unread_count,
                    'last_message': None,
                    'date': dialog.date.isoformat() if dialog.date else None
                }
                
                # Добавляем имя в зависимости от доступных атрибутов
                if hasattr(entity, 'first_name'):
                    dialog_info['name'] = entity.first_name
                    if hasattr(entity, 'last_name') and entity.last_name:
                        dialog_info['name'] += f" {entity.last_name}"
                
                # Если есть последнее сообщение, добавляем его информацию
                if dialog.message:
                    dialog_info['last_message'] = {
                        'id': dialog.message.id,
                        'text': dialog.message.text,
                        'date': dialog.message.date.isoformat() if dialog.message.date else None,
                        'out': dialog.message.out  # True если сообщение отправлено нами
                    }
                
                dialogs.append(dialog_info)
        
        return {
            'success': True,
            'dialogs': dialogs
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении диалогов: {str(e)}")
        return {'error': f'Ошибка при получении диалогов: {str(e)}'}

async def get_messages(phone, entity_id, limit=100):
    """
    Получает сообщения из указанного диалога
    
    phone: Номер телефона аккаунта
    entity_id: ID сущности (пользователя, группы, канала)
    limit: Максимальное количество сообщений для получения
    """
    if phone not in clients:
        return {'error': 'Аккаунт не авторизован'}
    
    client = clients[phone]
    
    try:
        # Получаем сущность по ID
        entity = await client.get_entity(entity_id)
        
        messages = []
        async for message in client.iter_messages(entity, limit=limit):
            message_info = {
                'id': message.id,
                'text': message.text,
                'date': message.date.isoformat() if message.date else None,
                'out': message.out,  # True если сообщение отправлено нами
                'sender_id': message.sender_id,
                'reply_to_msg_id': message.reply_to_msg_id
            }
            
            messages.append(message_info)
        
        # Сортируем сообщения по дате (от самых старых к новым)
        messages.sort(key=lambda x: x['date'])
        
        return {
            'success': True,
            'entity_id': entity_id,
            'messages': messages
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {str(e)}")
        return {'error': f'Ошибка при получении сообщений: {str(e)}'}

async def send_message_to_contact(phone, contact_id, message):
    """
    Отправляет сообщение контакту
    
    phone: Номер телефона аккаунта
    contact_id: ID контакта в Telegram
    message: Текст сообщения
    """
    if phone not in clients:
        return {'error': 'Аккаунт не авторизован'}
    
    client = clients[phone]
    
    try:
        # Отправляем сообщение
        entity = await client.get_entity(contact_id)
        sent_message = await client.send_message(entity, message)
        
        return {
            'success': True,
            'message_id': sent_message.id,
            'date': sent_message.date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {str(e)}")
        return {'error': f'Ошибка при отправке сообщения: {str(e)}'}

def run_async(coroutine):
    """
    Утилита для запуска асинхронных функций в синхронном контексте
    
    coroutine: Асинхронная функция (корутина)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()