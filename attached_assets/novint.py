import os
import sqlite3
import logging
import csv
import sys
import json
import time
import asyncio
import threading
import subprocess
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Callable

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit,
    QCheckBox, QListWidget, QGroupBox, QScrollArea, QGridLayout, QFileDialog,
    QInputDialog, QProgressDialog, QStyle, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='telegram_sender.log',
    filemode='a'
)

# Добавляем вывод логов в консоль для отладки
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)

logger = logging.getLogger('database')
message_logger = logging.getLogger('message_sender')
auth_logger = logging.getLogger('auth')
telegram_logger = logging.getLogger('telegram')

# Увеличиваем уровень логирования для библиотеки Telethon
telethon_logger = logging.getLogger('telethon')
telethon_logger.setLevel(logging.DEBUG)
telethon_logger.addHandler(console_handler)

DB_FILE = "telegram_sender.db"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = dict_factory
    return conn

def init_database():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            api_id TEXT NOT NULL,
            api_hash TEXT NOT NULL,
            delay INTEGER DEFAULT 1200,
            session_string TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            contact_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (contact_id) REFERENCES contacts (id),
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_timestamps (
            account_id INTEGER PRIMARY KEY,
            last_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')

        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

def add_account(phone: str, api_id: str, api_hash: str, delay: int = 1200) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO accounts (phone, api_id, api_hash, delay) VALUES (?, ?, ?, ?)",
            (phone, api_id, api_hash, delay)
        )

        account_id = cursor.lastrowid

        # Добавляем запись в таблицу таймстампов для аккаунта
        cursor.execute(
            "INSERT INTO account_timestamps (account_id) VALUES (?)",
            (account_id,)
        )

        conn.commit()
        logger.info(f"Added new account with ID {account_id}")
        return account_id if account_id is not None else 0
    except Exception as e:
        logger.error(f"Error adding account: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_account_session(account_id: int, session_string: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE accounts SET session_string = ? WHERE id = ?",
            (session_string, account_id)
        )

        conn.commit()
        success = cursor.rowcount > 0
        logger.info(f"Updated session for account {account_id}: {success}")
        return success
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_account_delay(account_id: int, delay: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE accounts SET delay = ? WHERE id = ?",
            (delay, account_id)
        )

        conn.commit()
        success = cursor.rowcount > 0
        logger.info(f"Updated delay for account {account_id} to {delay}s")
        return success
    except Exception as e:
        logger.error(f"Error updating delay: {e}")
        raise
    finally:
        if conn:
            conn.close()

def delete_account(account_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Удаляем запись из таблицы таймстампов
        cursor.execute("DELETE FROM account_timestamps WHERE account_id = ?", (account_id,))

        # Удаляем аккаунт
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))

        conn.commit()
        success = cursor.rowcount > 0
        logger.info(f"Deleted account {account_id}: {success}")
        return success
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_accounts() -> List[Dict[str, Any]]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts ORDER BY id")

        accounts = cursor.fetchall()
        return accounts
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_account(account_id: int) -> Optional[Dict[str, Any]]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))

        account = cursor.fetchone()
        return account
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def add_contact(name: str, phone: str) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO contacts (name, phone) VALUES (?, ?)",
            (name, phone)
        )

        contact_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Added new contact with ID {contact_id}")
        return contact_id if contact_id is not None else 0
    except Exception as e:
        logger.error(f"Error adding contact: {e}")
        raise
    finally:
        if conn:
            conn.close()

def delete_contact(contact_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))

        conn.commit()
        success = cursor.rowcount > 0
        logger.info(f"Deleted contact {contact_id}: {success}")
        return success
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_contacts() -> List[Dict[str, Any]]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM contacts ORDER BY name")

        contacts = cursor.fetchall()
        return contacts
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise
    finally:
        if conn:
            conn.close()

def save_message(text: str) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (text) VALUES (?)",
            (text,)
        )

        message_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Saved message with ID {message_id}")
        return message_id if message_id is not None else 0
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_message(message_id: int) -> Optional[Dict[str, Any]]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))

        message = cursor.fetchone()
        return message
    except Exception as e:
        logger.error(f"Error getting message {message_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_account_timestamp(account_id: int) -> bool:
    try:
        # Для отладки
        logger.debug(f"Updating timestamp for account {account_id}")
        
        conn = get_connection()
        cursor = conn.cursor()

        # Получаем текущее время (более явно для контроля)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"Current timestamp for account {account_id}: {current_time}")
        
        cursor.execute(
            "UPDATE account_timestamps SET last_sent = ? WHERE account_id = ?",
            (current_time, account_id)
        )

        if cursor.rowcount == 0:
            # Если записи нет, создаем
            cursor.execute(
                "INSERT INTO account_timestamps (account_id, last_sent) VALUES (?, CURRENT_TIMESTAMP)",
                (account_id,)
            )

        conn.commit()
        logger.info(f"Updated timestamp for account {account_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating timestamp: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_account_last_sent(account_id: int) -> Optional[str]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT last_sent FROM account_timestamps WHERE account_id = ?",
            (account_id,)
        )

        result = cursor.fetchone()
        if result:
            return result['last_sent']
        return None
    except Exception as e:
        logger.error(f"Error getting last sent time: {e}")
        return None
    finally:
        if conn:
            conn.close()

def record_sent_message(account_id: int, contact_id: int, message_id: int, status: str) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO sent_messages (account_id, contact_id, message_id, status) VALUES (?, ?, ?, ?)",
            (account_id, contact_id, message_id, status)
        )

        sent_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Recorded sent message with ID {sent_id} (status: {status})")

        # Обновляем таймстамп последней отправки для аккаунта только при успешной отправке
        # Проверяем оба варианта записи статуса (с одинарными и двойными кавычками)
        if status == 'sent' or status == "sent":
            logger.debug(f"Updating timestamp for account {account_id} after successful message")
            update_account_timestamp(account_id)
        else:
            logger.debug(f"Not updating timestamp for account {account_id} due to status: {status}")

        return sent_id if sent_id is not None else 0
    except Exception as e:
        logger.error(f"Error recording sent message: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_message_history() -> List[Dict[str, Any]]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sm.*, 
                   a.phone as account_phone, 
                   c.name as contact_name, 
                   c.phone as contact_phone,
                   m.text as message_text
            FROM sent_messages sm
            LEFT JOIN accounts a ON sm.account_id = a.id
            LEFT JOIN contacts c ON sm.contact_id = c.id
            LEFT JOIN messages m ON sm.message_id = m.id
            ORDER BY sm.sent_at DESC
        """)

        history = cursor.fetchall()
        return history
    except Exception as e:
        logger.error(f"Error getting message history: {e}")
        raise
    finally:
        if conn:
            conn.close()
            
def clear_message_history() -> bool:
    """Clear all message sending history"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sent_messages")
        conn.commit()
        
        logger.info("Message history cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing message history: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_account_delay(account_id: int) -> Tuple[bool, int]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Получаем информацию об аккаунте
        cursor.execute("SELECT delay FROM accounts WHERE id = ?", (account_id,))
        account = cursor.fetchone()

        if not account:
            logger.error(f"Account {account_id} not found")
            return False, 0

        delay = account['delay']
        
        # Для отладки - выводим задержку аккаунта
        logger.debug(f"Account {account_id} has delay setting: {delay} seconds")

        # Получаем таймстамп последней отправки
        last_sent = get_account_last_sent(account_id)
        
        # Для отладки - выводим таймстамп последней отправки
        logger.debug(f"Account {account_id} last sent timestamp: {last_sent}")

        if not last_sent:
            logger.info(f"No previous sends for account {account_id}")
            return True, 0

        # Вычисляем, сколько времени прошло
        try:
            # Конвертируем строку таймстампа в Unix timestamp
            last_sent_time = time.mktime(time.strptime(last_sent, '%Y-%m-%d %H:%M:%S'))
            current_time = time.time()
            elapsed = current_time - last_sent_time

            logger.info(f"Account {account_id}: elapsed {elapsed:.2f}s since last send, delay is {delay}s")

            if elapsed < delay:
                # Если прошло меньше времени, чем задержка
                remaining = delay - elapsed
                # Округляем оставшееся время вверх для гарантии соблюдения минимальной задержки
                remaining_seconds = int(remaining) + (1 if remaining > int(remaining) else 0)
                logger.info(f"Account {account_id}: need to wait {remaining_seconds}s more")
                return False, remaining_seconds
            else:
                logger.info(f"Account {account_id}: delay passed, can send")
                return True, 0
        except Exception as e:
            logger.error(f"Error calculating time: {e}")
            return True, 0  # В случае ошибки позволяем отправить
    except Exception as e:
        logger.error(f"Error checking account delay: {e}")
        return True, 0  # В случае ошибки позволяем отправить
    finally:
        if conn:
            conn.close()

@dataclass
class Account:
    id: int
    phone: str
    api_id: str
    api_hash: str
    delay: int = 1200
    session_string: Optional[str] = None
    active: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        return cls(
            id=data.get('id', 0),
            phone=data.get('phone', ''),
            api_id=data.get('api_id', ''),
            api_hash=data.get('api_hash', ''),
            delay=data.get('delay', 1200),
            session_string=data.get('session_string'),
            active=bool(data.get('session_string'))
        )

@dataclass
class Contact:
    id: int
    name: str
    phone: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            phone=data.get('phone', '')
        )

@dataclass
class Message:
    id: int
    text: str
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data.get('id', 0),
            text=data.get('text', ''),
            created_at=data.get('created_at', '')
        )

@dataclass
class SentMessage:
    id: int
    account_id: int
    contact_id: int
    message_id: int
    status: str
    sent_at: str

    account_phone: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    message_text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentMessage':
        return cls(
            id=data.get('id', 0),
            account_id=data.get('account_id', 0),
            contact_id=data.get('contact_id', 0),
            message_id=data.get('message_id', 0),
            status=data.get('status', ''),
            sent_at=data.get('sent_at', ''),
            account_phone=data.get('account_phone'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            message_text=data.get('message_text')
        )

class TelegramAccountClient:
    def __init__(self, account_data: Dict[str, Any]):
        self.account_id = account_data.get('id')
        self.phone = account_data.get('phone')
        self.api_id = account_data.get('api_id')
        self.api_hash = account_data.get('api_hash')
        self.session_string = account_data.get('session_string')
        self.delay = account_data.get('delay', 1200)

        self.client = None
        self._is_connected = False
        self._is_authorized = False

        os.makedirs('sessions', exist_ok=True)

    async def connect(self) -> bool:
        try:
            auth_logger.debug(f"Connecting with phone={self.phone}, api_id={self.api_id}")

            # Если нет строки сессии, подключаться не пытаемся
            if not self.session_string:
                auth_logger.debug(f"No session string for account {self.account_id}")
                return False

            session = StringSession(self.session_string)

            connection_settings = {
                'connection_retries': 5,
                'retry_delay': 1,
                'auto_reconnect': True,
                'request_retries': 5,
                'timeout': 60,
                'device_model': 'Desktop',
                'system_version': 'Windows',
                'app_version': '1.0',
                'lang_code': 'en',
            }

            self.client = TelegramClient(
                session, 
                int(self.api_id), 
                self.api_hash,
                **connection_settings
            )

            await self.client.connect()
            auth_logger.debug(f"Connected to Telegram API for {self.phone}")
            self._is_connected = True

            self._is_authorized = await self.client.is_user_authorized()
            auth_logger.debug(f"Is authorized: {self._is_authorized}")

            return self._is_connected
        except Exception as e:
            auth_logger.error(f"Error connecting to Telegram: {e}")
            self._is_connected = False
            return False

    async def is_authorized(self) -> bool:
        if not self._is_connected or not self.client:
            return False

        try:
            self._is_authorized = await self.client.is_user_authorized()
            return self._is_authorized
        except Exception as e:
            auth_logger.error(f"Error checking authorization: {e}")
            return False

    async def send_message(self, contact_identifier: str, text: str) -> Dict[str, Any]:
        if not self._is_connected or not self.client or not self._is_authorized:
            message_logger.error(f"Client not connected or not authorized. Connected: {self._is_connected}, Client: {bool(self.client)}, Authorized: {self._is_authorized}")
            return {"success": False, "error": "Client not connected or not authorized"}

        try:
            # Проверяем, это имя пользователя или телефон
            is_username = contact_identifier.startswith('@')

            if is_username:
                # Это имя пользователя, удаляем @ в начале
                username = contact_identifier.lstrip('@')
                message_logger.info(f"Attempting to send message to username: @{username}")

                try:
                    # Ищем пользователя по имени
                    entity = await self.client.get_entity(username)
                    message_logger.info(f"Found entity by username: {entity.id}")

                    # Отправляем сообщение
                    sent_message = await self.client.send_message(entity, text)
                    message_logger.info(f"Message sent successfully to @{username}, message_id: {sent_message.id}")

                    return {
                        "success": True,
                        "message_id": sent_message.id,
                        "date": sent_message.date.isoformat() if hasattr(sent_message, 'date') else ""
                    }

                except Exception as e:
                    message_logger.error(f"Error sending message to username @{username}: {e}")
                    return {"success": False, "error": f"Не удалось отправить сообщение пользователю @{username}: {str(e)}"}
            else:
                # Это телефонный номер, нормализуем его
                clean_phone = ''.join(c for c in contact_identifier if c.isdigit() or c == '+')
                if not clean_phone.startswith('+'):
                    clean_phone = '+' + clean_phone

                message_logger.info(f"Attempting to send message to phone: {clean_phone}")

                # Сначала пробуем добавить контакт
                try:
                    contact = InputPhoneContact(
                        client_id=0,
                        phone=clean_phone,
                        first_name="Contact",
                        last_name=""
                    )

                    # Импортируем контакт
                    message_logger.debug(f"Importing contact: {clean_phone}")
                    import_result = await self.client(ImportContactsRequest([contact]))
                    message_logger.info(f"Imported contact {clean_phone}, result: {import_result}")

                    # Если контакт был успешно импортирован
                    if import_result and import_result.users:
                        entity = import_result.users[0]
                        message_logger.info(f"Using imported contact as entity: {entity.id}")
                    else:
                        # Если импорт не удался, пробуем получить по номеру
                        message_logger.debug(f"Import didn't return users, trying direct get_entity")
                        entity = await self.client.get_entity(clean_phone)
                except Exception as e:
                    message_logger.warning(f"Failed to import contact {clean_phone}: {e}")
                    # Пробуем получить пользователя напрямую
                    try:
                        entity = await self.client.get_entity(clean_phone)
                        message_logger.info(f"Got entity directly: {entity}")
                    except Exception as e2:
                        message_logger.error(f"Could not get entity for {clean_phone}: {e2}")
                        return {"success": False, "error": f"Could not find user with phone {clean_phone}: {str(e2)}"}

                # Отправляем сообщение
                message_logger.debug(f"Sending message to entity: {entity}")
                sent_message = await self.client.send_message(entity, text)

                message_logger.info(f"Message sent successfully to {clean_phone}, message_id: {sent_message.id}")
                return {
                    "success": True,
                    "message_id": sent_message.id,
                    "date": sent_message.date.isoformat() if hasattr(sent_message, 'date') else ""
                }
        except Exception as e:
            message_logger.error(f"Error sending message to {contact_identifier}: {e}")
            return {"success": False, "error": str(e)}

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
                self._is_connected = False
                self._is_authorized = False
                auth_logger.debug(f"Disconnected client for {self.phone}")
            except Exception as e:
                auth_logger.error(f"Error disconnecting client for {self.phone}: {e}")

async def console_auth_tool(account_id: int, phone: str, api_id: str, api_hash: str) -> bool:
    print(f"Начало авторизации аккаунта {phone}")
    auth_logger.info(f"Starting authentication for account {phone}")

    # Создаем клиент Telegram
    session = StringSession()
    client = TelegramClient(
        session, 
        int(api_id), 
        api_hash,
        connection_retries=5,
        retry_delay=1,
        timeout=60
    )

    try:
        await client.connect()
        auth_logger.info(f"Connected to Telegram for authentication of {phone}")

        # Проверяем, авторизован ли уже клиент
        if await client.is_user_authorized():
            print("Аккаунт уже авторизован!")
            auth_logger.info(f"Account {phone} is already authorized")
            session_string = StringSession.save(client.session)
            update_account_session(account_id, session_string)
            return True

        # Запрашиваем код
        await client.send_code_request(phone)
        print(f"Код отправлен на номер {phone}")
        auth_logger.info(f"Authentication code sent to {phone}")

        # Получаем код от пользователя
        code = input("Введите код из Telegram: ")
        auth_logger.info(f"Code entered for {phone}")

        try:
            await client.sign_in(phone, code)
            auth_logger.info(f"Signed in successfully for {phone}")
        except SessionPasswordNeededError:
            print("Требуется пароль двухфакторной аутентификации")
            auth_logger.info(f"2FA required for {phone}")
            password = input("Введите пароль 2FA: ")
            await client.sign_in(password=password)
            auth_logger.info(f"2FA authentication successful for {phone}")

        # Сохраняем строку сессии
        session_string = StringSession.save(client.session)
        auth_logger.info(f"Saving session string for {phone}")
        update_account_session(account_id, session_string)
        print("Авторизация успешно завершена!")
        auth_logger.info(f"Authentication completed for {phone}")

        return True

    except Exception as e:
        print(f"Ошибка авторизации: {str(e)}")
        auth_logger.error(f"Authentication error for {phone}: {e}")
        return False
    finally:
        try:
            await client.disconnect()
            auth_logger.info(f"Disconnected authentication client for {phone}")
        except:
            auth_logger.error(f"Error disconnecting authentication client for {phone}")
            pass

class TelegramClientManager:
    def __init__(self):
        self.clients = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Запускаем event loop в отдельном потоке
        self.loop_thread = threading.Thread(target=self._run_event_loop)
        self.loop_thread.daemon = True
        self.loop_thread.start()

        auth_logger.info("TelegramClientManager initialized")

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_account(self, account_data: Dict[str, Any]) -> None:
        account_id = account_data.get('id')
        auth_logger.debug(f"Adding account {account_id} to client manager")
        self.clients[account_id] = TelegramAccountClient(account_data)

    def remove_account(self, account_id: int) -> None:
        if account_id in self.clients:
            client = self.clients[account_id]
            if hasattr(client, 'client') and client.client:
                try:
                    auth_logger.debug(f"Disconnecting client {account_id}")
                    asyncio.run_coroutine_threadsafe(client.disconnect(), self.loop)
                except:
                    auth_logger.error(f"Error disconnecting client {account_id}")
                    pass

            self.clients.pop(account_id, None)
            auth_logger.info(f"Removed account {account_id} from client manager")

    def get_client(self, account_id: int) -> Optional[TelegramAccountClient]:
        client = self.clients.get(account_id)
        if not client:
            auth_logger.warning(f"Client {account_id} not found in manager")
        return client

    def connect_client(self, account_id: int) -> bool:
        client = self.get_client(account_id)
        if not client:
            auth_logger.error(f"Client {account_id} not found in manager")
            return False

        try:
            auth_logger.debug(f"Connecting client {account_id}")
            # Проверяем, есть ли у клиента строка сессии
            if not client.session_string:
                auth_logger.debug(f"Client {account_id} has no session string, not connecting")
                return False

            future = asyncio.run_coroutine_threadsafe(client.connect(), self.loop)
            result = future.result(timeout=60)  # Увеличен таймаут
            auth_logger.debug(f"Client {account_id} connection result: {result}")
            return result
        except Exception as e:
            auth_logger.error(f"Error connecting client {account_id}: {e}")
            return False

    def is_client_authorized(self, account_id: int) -> bool:
        client = self.get_client(account_id)
        if not client:
            return False

        # Если нет строки сессии, считаем, что клиент не авторизован
        if not client.session_string:
            return False

        try:
            future = asyncio.run_coroutine_threadsafe(client.is_authorized(), self.loop)
            return future.result(timeout=30)  # Увеличен таймаут
        except Exception as e:
            auth_logger.error(f"Error checking if client {account_id} is authorized: {e}")
            return False

    def disconnect_all(self) -> None:
        for account_id, client in self.clients.items():
            try:
                auth_logger.debug(f"Disconnecting client {account_id}")
                asyncio.run_coroutine_threadsafe(client.disconnect(), self.loop)
            except Exception as e:
                auth_logger.error(f"Error disconnecting client {account_id}: {e}")

    def get_available_clients(self) -> List[int]:
        available_clients = []
        for account_id, client in self.clients.items():
            # Проверяем только наличие строки сессии
            if client.session_string:
                available_clients.append(account_id)
                auth_logger.debug(f"Client {account_id} is available")
            else:
                auth_logger.debug(f"Client {account_id} is not available (no session string)")

        auth_logger.info(f"Found {len(available_clients)} available clients: {available_clients}")
        return available_clients

    def update_client_delay(self, account_id: int, delay: int) -> None:
        client = self.get_client(account_id)
        if client:
            client.delay = delay
            auth_logger.info(f"Updated delay for client {account_id} to {delay}s")

    def authorize_account(self, account_id: int, use_gui=True) -> bool:
        account = get_account(account_id)
        if not account:
            auth_logger.error(f"Account {account_id} not found in database")
            return False

        # Используем консольную авторизацию
        auth_logger.info(f"Starting console authentication for account {account_id}")
        success = asyncio.run(console_auth_tool(
            account_id,
            account['phone'],
            account['api_id'],
            account['api_hash']
        ))

        if success:
            # Обновляем аккаунт в менеджере
            updated_account = get_account(account_id)
            if updated_account and updated_account.get('session_string'):
                auth_logger.info(f"Authentication successful for account {account_id}, updating client")
                self.remove_account(account_id)  # Удаляем старый клиент
                self.add_account(updated_account)  # Добавляем новый с сессией

                # Проверяем подключение
                auth_logger.info(f"Testing connection for newly authorized account {account_id}")
                connection_result = self.connect_client(account_id)
                auth_logger.info(f"Connection test for account {account_id}: {connection_result}")

                return True
            else:
                auth_logger.error(f"Authentication succeeded but no session string found for account {account_id}")
        else:
            auth_logger.error(f"Authentication failed for account {account_id}")

        return False

    async def send_message_directly(self, account_id: int, contact_identifier: str, message_text: str) -> Dict[str, Any]:
        client = self.get_client(account_id)
        if not client:
            message_logger.error(f"Client {account_id} not found")
            return {"success": False, "error": "Client not found"}
            
        # Мы удаляем проверку задержки здесь, так как она уже выполняется в основном коде отправки
        # и мы ожидаем необходимое время перед вызовом этой функции

        # Подключаем клиент, если еще не подключен
        if not client._is_connected:
            connect_result = await client.connect()
            if not connect_result:
                message_logger.error(f"Failed to connect client {account_id}")
                return {"success": False, "error": "Failed to connect client"}

        # Отправляем сообщение
        result = await client.send_message(contact_identifier, message_text)
        message_logger.info(f"Direct message sending result: {result}")

        return result

    def send_message_sync(self, account_id: int, contact_identifier: str, message_text: str) -> Dict[str, Any]:
        future = asyncio.run_coroutine_threadsafe(
            self.send_message_directly(account_id, contact_identifier, message_text),
            self.loop
        )

        try:
            result = future.result(timeout=60)
            return result
        except Exception as e:
            message_logger.error(f"Error in send_message_sync: {e}")
            return {"success": False, "error": str(e)}

class AccountsTab(QWidget):
    accounts_changed = pyqtSignal()

    def __init__(self, client_manager):
        super().__init__()
        self.client_manager = client_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_label = QLabel('Управление Telegram аккаунтами')
        header_label.setStyleSheet('font-size: 16pt; font-weight: bold;')
        header_layout.addWidget(header_label)

        add_button = QPushButton('Добавить аккаунт')
        add_button.clicked.connect(self.add_account)
        header_layout.addWidget(add_button, alignment=Qt.AlignRight)

        layout.addLayout(header_layout)

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels(['ID', 'Телефон', 'API ID', 'Задержка (сек)', 'Статус', 'Действия'])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.accounts_table.doubleClicked.connect(self.on_table_double_clicked)

        layout.addWidget(self.accounts_table)

        instructions = QLabel(
            'Для работы с Telegram API необходимо:\n'
            '1. Получить API ID и API Hash на сайте https://my.telegram.org/apps\n'
            '2. Добавить аккаунт, указав номер телефона, API ID и API Hash\n'
            '3. Следовать инструкциям для авторизации (ввести код из Telegram и пароль, если требуется)'
        )
        instructions.setStyleSheet('background-color: #f0f0f0; padding: 10px; border-radius: 5px;')
        layout.addWidget(instructions)

        self.setLayout(layout)

        self.load_accounts()

    def load_accounts(self):
        accounts = get_accounts()

        self.accounts_table.setRowCount(len(accounts))

        for i, account in enumerate(accounts):
            id_item = QTableWidgetItem(str(account['id']))
            self.accounts_table.setItem(i, 0, id_item)

            phone_item = QTableWidgetItem(account['phone'])
            self.accounts_table.setItem(i, 1, phone_item)

            api_id_item = QTableWidgetItem(account['api_id'])
            self.accounts_table.setItem(i, 2, api_id_item)

            delay_item = QTableWidgetItem(str(account['delay']))
            self.accounts_table.setItem(i, 3, delay_item)

            status_text = 'Авторизован' if account['session_string'] else 'Не авторизован'
            status_item = QTableWidgetItem(status_text)
            if account['session_string']:
                status_item.setBackground(Qt.green)
            else:
                status_item.setBackground(Qt.yellow)
            self.accounts_table.setItem(i, 4, status_item)

            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)

            authorize_button = QPushButton('Авторизовать')
            authorize_button.setProperty('account_id', account['id'])
            authorize_button.clicked.connect(self.authorize_account)
            actions_layout.addWidget(authorize_button)

            change_delay_button = QPushButton('Изменить задержку')
            change_delay_button.setProperty('account_id', account['id'])
            change_delay_button.clicked.connect(self.change_delay)
            actions_layout.addWidget(change_delay_button)

            delete_button = QPushButton('Удалить')
            delete_button.setProperty('account_id', account['id'])
            delete_button.clicked.connect(self.delete_account)
            actions_layout.addWidget(delete_button)

            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            self.accounts_table.setCellWidget(i, 5, actions_widget)

    def add_account(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Добавление Telegram аккаунта')
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        phone_input = QLineEdit()
        phone_input.setPlaceholderText('+79001234567')
        layout.addRow('Номер телефона:', phone_input)

        api_id_input = QLineEdit()
        layout.addRow('API ID:', api_id_input)

        api_hash_input = QLineEdit()
        layout.addRow('API Hash:', api_hash_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec_() == QDialog.Accepted:
            phone = phone_input.text().strip()
            api_id = api_id_input.text().strip()
            api_hash = api_hash_input.text().strip()

            if not phone or not api_id or not api_hash:
                QMessageBox.warning(self, 'Ошибка', 'Все поля должны быть заполнены!')
                return

            try:
                account_id = add_account(phone, api_id, api_hash)

                account_data = get_account(account_id)
                if not account_data:
                    QMessageBox.critical(self, 'Ошибка', 'Не удалось получить данные аккаунта после добавления!')
                    return

                self.client_manager.add_account(account_data)

                self.load_accounts()

                self.accounts_changed.emit()

                QMessageBox.information(self, 'Успех', f'Аккаунт {phone} успешно добавлен!')

                # Автоматически запускаем авторизацию
                self.authorize_account(account_id)

            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить аккаунт: {str(e)}')

    def change_delay(self):
        sender = self.sender()
        if not sender:
            return

        account_id = sender.property('account_id')
        if not account_id:
            return

        account = get_account(account_id)
        if not account:
            QMessageBox.warning(self, 'Ошибка', 'Аккаунт не найден!')
            return

        current_delay = account['delay']

        new_delay, ok = QInputDialog.getInt(
            self, 'Изменение задержки', 
            f'Введите новую задержку для аккаунта {account["phone"]} (в секундах):',
            value=current_delay, min=1, max=3600
        )

        if ok:
            try:
                update_account_delay(account_id, new_delay)

                self.client_manager.update_client_delay(account_id, new_delay)

                self.load_accounts()

                QMessageBox.information(
                    self, 'Успех', 
                    f'Задержка для аккаунта {account["phone"]} успешно обновлена на {new_delay} сек!'
                )
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить задержку: {str(e)}')

    def get_selected_account_id(self):
        selected_rows = self.accounts_table.selectedItems()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        id_item = self.accounts_table.item(row, 0)

        return int(id_item.text())

    def on_table_double_clicked(self, index):
        if index.column() != 5:
            account_id = int(self.accounts_table.item(index.row(), 0).text())

            status_item = self.accounts_table.item(index.row(), 4)
            is_authorized = status_item.text() == 'Авторизован'

            if not is_authorized:
                self.authorize_account(account_id)

    def authorize_account(self, account_id=None, use_gui=False):
        if account_id is None:
            sender = self.sender()
            if sender:
                account_id = sender.property('account_id')

            if account_id is None:
                account_id = self.get_selected_account_id()

        if account_id is None:
            QMessageBox.warning(self, 'Ошибка', 'Выберите аккаунт для авторизации!')
            return

        account = get_account(account_id)
        if not account:
            QMessageBox.warning(self, 'Ошибка', f'Аккаунт с ID {account_id} не найден в базе данных!')
            return

        QMessageBox.information(
            self, 
            'Авторизация через консоль', 
            f'Сейчас будет начата авторизация для аккаунта {account["phone"]}.\n\n'
            f'Проверьте консоль - вам нужно будет ввести код подтверждения, '
            f'который придёт на ваш телефон. При необходимости также введите пароль 2FA.'
        )

        # Запускаем прогресс-диалог
        progress = QProgressDialog("Авторизация аккаунта...", "Отмена", 0, 0, self)
        progress.setWindowTitle("Авторизация")
        progress.setLabelText(f"Авторизация аккаунта {account['phone']}...\nПерейдите в консоль для ввода кода.")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        # Запускаем авторизацию через менеджер клиентов
        success = self.client_manager.authorize_account(account_id, use_gui=False)

        progress.close()

        if success:
            QMessageBox.information(self, 'Успех', 'Аккаунт успешно авторизован!')
            self.load_accounts()
            self.accounts_changed.emit()
        else:
            QMessageBox.critical(self, 'Ошибка авторизации', 'Не удалось авторизовать аккаунт. Проверьте консоль для деталей.')

    def delete_account(self):
        sender = self.sender()
        if sender:
            account_id = sender.property('account_id')
        else:
            account_id = self.get_selected_account_id()

        if account_id is None:
            QMessageBox.warning(self, 'Ошибка', 'Выберите аккаунт для удаления!')
            return

        confirm = QMessageBox.question(
            self, 'Подтверждение', 
            'Вы уверены, что хотите удалить этот аккаунт?',
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                self.client_manager.remove_account(account_id)

                delete_account(account_id)

                self.load_accounts()

                self.accounts_changed.emit()

                QMessageBox.information(self, 'Успех', 'Аккаунт успешно удален!')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить аккаунт: {str(e)}')

class ContactsTab(QWidget):
    contacts_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_label = QLabel('Управление контактами')
        header_label.setStyleSheet('font-size: 16pt; font-weight: bold;')
        header_layout.addWidget(header_label)

        buttons_layout = QHBoxLayout()

        add_button = QPushButton('Добавить контакт')
        add_button.clicked.connect(self.add_contact)
        buttons_layout.addWidget(add_button)

        add_multi_button = QPushButton('Добавить список')
        add_multi_button.clicked.connect(self.add_bulk_contacts)
        buttons_layout.addWidget(add_multi_button)

        import_csv_button = QPushButton('Импорт из CSV')
        import_csv_button.clicked.connect(lambda: self.import_contacts("csv"))
        buttons_layout.addWidget(import_csv_button)

        import_txt_button = QPushButton('Импорт из TXT')
        import_txt_button.clicked.connect(lambda: self.import_contacts("txt"))
        buttons_layout.addWidget(import_txt_button)

        export_button = QPushButton('Экспорт в CSV')
        export_button.clicked.connect(self.export_contacts)
        buttons_layout.addWidget(export_button)

        header_layout.addLayout(buttons_layout)

        layout.addLayout(header_layout)

        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(['ID', 'Имя', 'Контакт', 'Действия'])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.contacts_table.doubleClicked.connect(self.on_table_double_clicked)

        layout.addWidget(self.contacts_table)

        info_label = QLabel('Введите имя пользователя в формате @username или номер телефона в международном формате: +79001234567')
        info_label.setStyleSheet('background-color: #f0f0f0; padding: 10px; border-radius: 5px;')
        layout.addWidget(info_label)

        self.setLayout(layout)

        self.load_contacts()

    def load_contacts(self):
        contacts = get_contacts()

        self.contacts_table.setRowCount(len(contacts))

        for i, contact in enumerate(contacts):
            id_item = QTableWidgetItem(str(contact['id']))
            self.contacts_table.setItem(i, 0, id_item)

            name_item = QTableWidgetItem(contact['name'])
            self.contacts_table.setItem(i, 1, name_item)

            phone_item = QTableWidgetItem(contact['phone'])
            self.contacts_table.setItem(i, 2, phone_item)

            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)

            delete_button = QPushButton('Удалить')
            delete_button.setProperty('contact_id', contact['id'])
            delete_button.clicked.connect(self.delete_contact)
            actions_layout.addWidget(delete_button)

            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            self.contacts_table.setCellWidget(i, 3, actions_widget)

    def add_contact(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Добавление контакта')
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        layout.addRow('Имя:', name_input)

        contact_input = QLineEdit()
        contact_input.setPlaceholderText('@username или +79001234567')
        layout.addRow('Telegram:', contact_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            contact = contact_input.text().strip()

            if not name or not contact:
                QMessageBox.warning(self, 'Ошибка', 'Имя и контакт не могут быть пустыми!')
                return

            try:
                add_contact(name, contact)

                self.load_contacts()

                self.contacts_changed.emit()

                QMessageBox.information(self, 'Успех', f'Контакт {name} успешно добавлен!')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить контакт: {str(e)}')

    def add_bulk_contacts(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Добавление списка контактов')
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        info_label = QLabel('Введите список контактов, по одному в строке.\n'
                          'Формат: @username или +79001234567\n'
                          'Чтобы добавить имя, укажите его после контакта через пробел.')
        layout.addWidget(info_label)

        contacts_input = QTextEdit()
        contacts_input.setPlaceholderText('@username1\n@username2 Имя пользователя\n+79001234567\n+79001234568 Иван')
        layout.addWidget(contacts_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            contacts_text = contacts_input.toPlainText().strip()

            if not contacts_text:
                QMessageBox.warning(self, 'Ошибка', 'Список контактов не может быть пустым!')
                return

            # Разбиваем на строки
            contact_lines = contacts_text.split('\n')
            successful = 0
            failed = 0

            for line in contact_lines:
                line = line.strip()
                if not line:
                    continue

                # Разбиваем по пробелу, первый элемент - контакт, остальное - имя
                parts = line.split(' ', 1)
                contact_id = parts[0].strip()

                # Если имя не указано, используем сам идентификатор
                if len(parts) > 1:
                    name = parts[1].strip()
                else:
                    # Если это username, отображаем без @
                    if contact_id.startswith('@'):
                        name = contact_id[1:] 
                    else:
                        name = contact_id

                try:
                    add_contact(name, contact_id)
                    successful += 1
                except Exception as e:
                    logger.error(f"Error adding contact {contact_id}: {e}")
                    failed += 1

            self.load_contacts()
            self.contacts_changed.emit()

            result_message = f'Успешно добавлено контактов: {successful}'
            if failed > 0:
                result_message += f'\nНе удалось добавить: {failed}'

            QMessageBox.information(self, 'Результат добавления', result_message)

    def get_selected_contact_id(self):
        selected_rows = self.contacts_table.selectedItems()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        id_item = self.contacts_table.item(row, 0)

        return int(id_item.text())

    def on_table_double_clicked(self, index):
        pass

    def delete_contact(self):
        sender = self.sender()
        if sender:
            contact_id = sender.property('contact_id')
        else:
            contact_id = self.get_selected_contact_id()

        if contact_id is None:
            QMessageBox.warning(self, 'Ошибка', 'Выберите контакт для удаления!')
            return

        confirm = QMessageBox.question(
            self, 'Подтверждение', 
            'Вы уверены, что хотите удалить этот контакт?',
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                delete_contact(contact_id)

                self.load_contacts()

                self.contacts_changed.emit()

                QMessageBox.information(self, 'Успех', 'Контакт успешно удален!')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить контакт: {str(e)}')

    def import_contacts(self, format_type):
        if format_type == "csv":
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Выберите CSV файл', '', 'CSV Files (*.csv)'
            )
        else:  # txt
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Выберите TXT файл', '', 'Text Files (*.txt)'
            )

        if not file_path:
            return

        try:
            count = 0

            if format_type == "csv":
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Пропускаем заголовок

                    for row in reader:
                        if len(row) >= 2:
                            name, contact = row[0], row[1]
                            add_contact(name, contact)
                            count += 1
            else:  # txt
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                    for line in lines:
                        line = line.strip()
                        if line:
                            # Разделяем по первому пробелу или табуляции
                            parts = line.split(None, 1)
                            if len(parts) == 2:
                                contact, name = parts
                            else:
                                # Если есть только одна часть, считаем её контактом
                                contact = parts[0]
                                # Если это username, отображаем без @
                                if contact.startswith('@'):
                                    name = contact[1:]
                                else:
                                    name = f"Контакт {count+1}"

                            add_contact(name, contact)
                            count += 1

            self.load_contacts()

            self.contacts_changed.emit()

            QMessageBox.information(self, 'Успех', f'Импортировано {count} контактов!')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось импортировать контакты: {str(e)}')

    def export_contacts(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить CSV файл', '', 'CSV Files (*.csv)'
        )

        if not file_path:
            return

        try:
            contacts = get_contacts()

            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Имя', 'Контакт'])

                for contact in contacts:
                    writer.writerow([contact['name'], contact['phone']])

            QMessageBox.information(self, 'Успех', f'Экспортировано {len(contacts)} контактов!')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать контакты: {str(e)}')

class MessagesTab(QWidget):
    def __init__(self, client_manager):
        super().__init__()
        self.client_manager = client_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header_label = QLabel('Отправка сообщений')
        header_label.setStyleSheet('font-size: 16pt; font-weight: bold;')
        layout.addWidget(header_label)

        content_layout = QHBoxLayout()

        left_panel = QVBoxLayout()

        message_group = QGroupBox('Текст сообщения')
        message_layout = QVBoxLayout(message_group)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText('Введите текст сообщения...')
        message_layout.addWidget(self.message_input)

        left_panel.addWidget(message_group)

        accounts_group = QGroupBox('Доступные аккаунты')
        accounts_layout = QVBoxLayout(accounts_group)

        self.accounts_list = QListWidget()
        accounts_layout.addWidget(self.accounts_list)

        # Добавляем настройки задержки для аккаунтов
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Задержка между сообщениями (сек):")
        self.delay_input = QSpinBox()
        self.delay_input.setMinimum(1)
        self.delay_input.setMaximum(3600)
        self.delay_input.setValue(1200)  # 20 минут
        self.update_delay_button = QPushButton("Применить ко всем")
        self.update_delay_button.clicked.connect(self.update_all_delays)

        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_input)
        delay_layout.addWidget(self.update_delay_button)

        accounts_layout.addLayout(delay_layout)

        left_panel.addWidget(accounts_group)

        right_panel = QVBoxLayout()

        contacts_group = QGroupBox('Выберите контакты для отправки')
        contacts_layout = QVBoxLayout(contacts_group)

        select_all_layout = QHBoxLayout()
        self.select_all_button = QPushButton('Выбрать все')
        self.select_all_button.clicked.connect(self.select_all_contacts_clicked)
        select_all_layout.addWidget(self.select_all_button, alignment=Qt.AlignRight)
        contacts_layout.addLayout(select_all_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        contacts_container = QWidget()
        self.contacts_layout = QGridLayout(contacts_container)
        self.contacts_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(contacts_container)
        contacts_layout.addWidget(scroll_area)

        right_panel.addWidget(contacts_group)

        content_layout.addLayout(left_panel, 1)
        content_layout.addLayout(right_panel, 1)

        layout.addLayout(content_layout)

        send_layout = QHBoxLayout()

        self.send_button = QPushButton('Отправить сообщения')
        self.send_button.setStyleSheet('font-size: 14pt; padding: 10px;')
        self.send_button.setMinimumWidth(200)
        self.send_button.clicked.connect(self.send_messages)
        send_layout.addWidget(self.send_button, alignment=Qt.AlignRight)

        layout.addLayout(send_layout)

        history_group = QGroupBox('История отправленных сообщений')
        history_layout = QVBoxLayout(history_group)
        
        # Добавляем кнопки для управления историей
        history_buttons_layout = QHBoxLayout()
        
        self.clear_history_button = QPushButton('Очистить историю')
        self.clear_history_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.clear_history_button.clicked.connect(self.clear_message_history)
        
        self.refresh_history_button = QPushButton('Обновить')
        self.refresh_history_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_history_button.clicked.connect(self.load_message_history)
        
        history_buttons_layout.addWidget(self.refresh_history_button)
        history_buttons_layout.addWidget(self.clear_history_button)
        history_buttons_layout.addStretch(1)  # Добавляем пружину для выравнивания кнопок влево
        
        history_layout.addLayout(history_buttons_layout)

        # Таблица истории
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(['Дата', 'Аккаунт', 'Контакт', 'Сообщение', 'Статус'])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)  # Чередующиеся цвета строк
        
        # Добавляем стиль для округлых краев и границ ячеек
        self.history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d3d3d3;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #d3d3d3;
                font-weight: bold;
            }
        """)
        
        history_layout.addWidget(self.history_table)

        layout.addWidget(history_group)

        self.setLayout(layout)

        self.update_account_list()
        self.update_contact_list()
        self.load_message_history()

    def update_account_list(self):
        self.accounts_list.clear()

        accounts = get_accounts()
        available_clients = self.client_manager.get_available_clients()

        for account in accounts:
            status = "✓ " if account['id'] in available_clients else "✗ "
            self.accounts_list.addItem(f"{status}{account['phone']} (задержка: {account['delay']}с)")

    def update_contact_list(self):
        while self.contacts_layout.count():
            item = self.contacts_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        contacts = get_contacts()

        self.contact_checkboxes = {}

        row = 0
        col = 0
        max_cols = 2

        for contact in contacts:
            checkbox = QCheckBox(f"{contact['name']} ({contact['phone']})")
            checkbox.setProperty('contact_id', contact['id'])
            checkbox.setProperty('contact_identifier', contact['phone'])
            self.contact_checkboxes[contact['id']] = checkbox

            self.contacts_layout.addWidget(checkbox, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def load_message_history(self):
        history = get_message_history()

        self.history_table.setRowCount(len(history))

        for i, record in enumerate(history):
            date_item = QTableWidgetItem(record['sent_at'])
            self.history_table.setItem(i, 0, date_item)

            account_item = QTableWidgetItem(record['account_phone'] or 'Неизвестно')
            self.history_table.setItem(i, 1, account_item)

            contact_name = record['contact_name'] or 'Неизвестно'
            contact_phone = record['contact_phone'] or 'Неизвестно'
            contact_item = QTableWidgetItem(f"{contact_name} ({contact_phone})")
            self.history_table.setItem(i, 2, contact_item)

            message_item = QTableWidgetItem(record['message_text'] or 'Неизвестно')
            self.history_table.setItem(i, 3, message_item)

            status_item = QTableWidgetItem(record['status'])
            if record['status'] == 'sent':
                status_item.setText('Отправлено')
                status_item.setBackground(Qt.green)
            elif record['status'] == 'failed':
                status_item.setText('Ошибка')
                status_item.setBackground(Qt.red)
            else:
                status_item.setText('В очереди')
                status_item.setBackground(Qt.yellow)
            self.history_table.setItem(i, 4, status_item)
            
    def clear_message_history(self):
        confirm = QMessageBox.question(
            self, 'Подтверждение', 
            'Вы уверены, что хотите очистить всю историю отправленных сообщений?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Из-за конфликта имен используем явный импорт функции
            from main import clear_message_history as clear_history_func
            if clear_history_func():
                self.load_message_history()
                QMessageBox.information(self, 'Успех', 'История сообщений успешно очищена')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось очистить историю сообщений')

    def select_all_contacts_clicked(self):
        for checkbox in self.contact_checkboxes.values():
            checkbox.setChecked(True)

    def update_all_delays(self):
        delay = self.delay_input.value()

        confirm = QMessageBox.question(
            self, 'Подтверждение', 
            f'Вы уверены, что хотите установить задержку {delay} секунд для всех аккаунтов?',
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            accounts = get_accounts()

            for account in accounts:
                try:
                    update_account_delay(account['id'], delay)
                    self.client_manager.update_client_delay(account['id'], delay)
                except Exception as e:
                    logger.error(f"Error updating delay for account {account['id']}: {e}")

            self.update_account_list()

            QMessageBox.information(self, 'Успех', f'Задержка обновлена для всех аккаунтов на {delay} сек!')

    def send_messages(self):
        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            QMessageBox.warning(self, 'Ошибка', 'Введите текст сообщения!')
            return

        selected_contacts = []
        for contact_id, checkbox in self.contact_checkboxes.items():
            if checkbox.isChecked():
                selected_contacts.append({
                    'id': contact_id, 
                    'identifier': checkbox.property('contact_identifier')
                })

        if not selected_contacts:
            QMessageBox.warning(self, 'Ошибка', 'Выберите хотя бы один контакт!')
            return

        available_clients = self.client_manager.get_available_clients()
        if not available_clients:
            QMessageBox.warning(self, 'Ошибка', 'Нет доступных аккаунтов для отправки сообщений! Авторизуйте хотя бы один аккаунт.')
            return

        # Сохраняем сообщение
        message_id = save_message(message_text)
        message_logger.info(f"Saved message with ID {message_id}")

        # Создаем встроенную прогресс-панель вместо модального диалога
        if not hasattr(self, 'progress_group') or not self.progress_group:
            # Создаем группу для отображения прогресса, если она еще не создана
            self.progress_group = QGroupBox('Прогресс отправки сообщений')
            self.progress_layout = QVBoxLayout(self.progress_group)
            
            # Добавляем индикатор статуса
            self.progress_status = QLabel("Подготовка к отправке...")
            self.progress_status.setStyleSheet("font-weight: bold; color: #333;")
            self.progress_layout.addWidget(self.progress_status)
            
            # Добавляем прогресс-бар
            self.progress_bar = QProgressBar()
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 5px;
                }
            """)
            self.progress_layout.addWidget(self.progress_bar)
            
            # Добавляем детальную информацию
            self.progress_details = QLabel("")
            self.progress_layout.addWidget(self.progress_details)
            
            # Добавляем статистику отправки
            self.progress_stats = QLabel("")
            self.progress_stats.setStyleSheet("font-size: 11pt; margin-top: 10px;")
            self.progress_layout.addWidget(self.progress_stats)
            
            # Добавляем группу с прогрессом в основной макет
            self.layout().addWidget(self.progress_group)
            
            # Изначально скрываем группу
            self.progress_group.hide()
        
        # Настраиваем отображение прогресса
        self.progress_group.show()
        self.progress_bar.setRange(0, len(selected_contacts))
        self.progress_bar.setValue(0)
        self.progress_status.setText("Начало отправки сообщений...")
        self.progress_details.setText("")
        self.progress_stats.setText("")
        QApplication.processEvents()

        # Распределяем контакты между аккаунтами "волнами"
        batches = {}  # account_id -> list of contacts

        # Инициализируем списки для каждого аккаунта
        for account_id in available_clients:
            batches[account_id] = []
        
        # Сортируем контакты по идентификаторам (для стабильности распределения)
        sorted_contacts = sorted(selected_contacts, key=lambda x: x['id'])
        
        # Распределяем контакты "волнами" по одному контакту на аккаунт за раз
        contact_index = 0
        while contact_index < len(sorted_contacts):
            # Проходим по всем доступным аккаунтам в этой волне
            for account_id in available_clients:
                # Если еще остались контакты для распределения
                if contact_index < len(sorted_contacts):
                    # Добавляем следующий контакт в очередь этого аккаунта
                    batches[account_id].append(sorted_contacts[contact_index])
                    contact_index += 1
                else:
                    # Все контакты распределены
                    break

        total_sent = 0
        success_count = 0
        fail_count = 0
        
        # Определяем максимальное количество волн
        max_waves = max([len(contacts) for account_id, contacts in batches.items()]) if batches else 0
        message_logger.info(f"Sending in {max_waves} waves")
        
        # Отправляем сообщения по волнам
        for wave in range(max_waves):
            message_logger.info(f"Starting wave {wave+1} of {max_waves}")
            
            # В каждой волне проходим по всем аккаунтам
            for account_id, contacts in batches.items():
                # Проверяем, есть ли у этого аккаунта контакт для текущей волны
                if wave < len(contacts):
                    account = get_account(account_id)
                    if not account:
                        continue
                        
                    contact = contacts[wave]
                    contact_id = contact['id']
                    contact_identifier = contact['identifier']
                    
                    # Обновляем прогресс-бар
                    self.progress_bar.setValue(total_sent)
                    self.progress_status.setText(f"Волна {wave+1}/{max_waves}: Отправка сообщений...")
                    self.progress_details.setText(f"Отправка сообщения контакту {contact_identifier} с аккаунта {account['phone']}")
                    self.progress_stats.setText(f"Отправлено: {success_count}, Ошибок: {fail_count}")
                    QApplication.processEvents()
                    
                    # Проверяем, соблюдена ли задержка для этого аккаунта
                    can_send, wait_time = check_account_delay(account_id)
                    if not can_send:
                        message_logger.info(f"Account {account_id} needs to wait {wait_time}s before sending")
                        
                        # Реально ждем всю необходимую задержку (важно для правильной работы "волнового" алгоритма)
                        self.progress_status.setText(f"Волна {wave+1}/{max_waves}: Ожидание задержки...")
                        self.progress_details.setText(f"Аккаунт {account['phone']} должен подождать {wait_time} сек.")
                        QApplication.processEvents()
                        
                        # Сон с периодическим обновлением интерфейса
                        for i in range(wait_time):
                            if i % 5 == 0 or i == wait_time - 1:  # Обновляем каждые 5 секунд и на последней секунде
                                self.progress_details.setText(f"Аккаунт {account['phone']} должен подождать {wait_time - i} сек.")
                                QApplication.processEvents()
                            time.sleep(1)
                    
                    # Отправляем сообщение
                    message_logger.info(f"Sending message from account {account_id} to contact {contact_id} in wave {wave+1}")
                    result = self.client_manager.send_message_sync(account_id, contact_identifier, message_text)
                    
                    # Обрабатываем результат отправки
                    if result.get('success'):
                        # Сначала записываем сообщение с статусом 'sent'
                        message_logger.debug(f"Recording successful message from account {account_id} to contact {contact_id}")
                        record_sent_message(account_id, contact_id, message_id, 'sent')
                        
                        # Обновляем таймстамп аккаунта для поддержания правильных задержек
                        message_logger.debug(f"Explicitly updating timestamp for account {account_id} after sending")
                        update_account_timestamp(account_id)
                        
                        success_count += 1
                        message_logger.info(f"Message sent successfully from account {account_id} to contact {contact_id} in wave {wave+1}")
                    else:
                        # Определяем тип ошибки
                        error = result.get('error', 'Unknown error')
                        
                        # Если ошибка связана с флудом от Telegram API
                        if 'flood' in error.lower() and 'wait' in error.lower():
                            message_logger.warning(f"Telegram flood control triggered for account {account_id}: {error}")
                            
                            # Извлекаем время ожидания из сообщения ошибки
                            import re
                            wait_match = re.search(r'(\d+)', error)
                            if wait_match:
                                extra_wait = int(wait_match.group(1))
                                message_logger.info(f"Need to wait extra {extra_wait} seconds for account {account_id}")
                                
                                # Ждем указанное Telegram время
                                self.progress_status.setText(f"Волна {wave+1}/{max_waves}: Ожидание Telegram...")
                                self.progress_details.setText(f"Telegram требует подождать для аккаунта {account['phone']}: {extra_wait} сек.")
                                QApplication.processEvents()
                                
                                # Сон с периодическим обновлением интерфейса
                                for i in range(min(extra_wait, 120)):  # Не более 2 минут максимум
                                    if i % 5 == 0 or i == extra_wait - 1:
                                        self.progress_details.setText(f"Telegram требует подождать для аккаунта {account['phone']}: {extra_wait - i} сек.")
                                        QApplication.processEvents()
                                    time.sleep(1)
                                
                                # Пробуем отправить снова
                                message_logger.info(f"Retrying message sending after waiting for account {account_id}")
                                result = self.client_manager.send_message_sync(account_id, contact_identifier, message_text)
                                
                                if result.get('success'):
                                    message_logger.debug(f"Message sent successfully after retry for account {account_id}")
                                    record_sent_message(account_id, contact_id, message_id, 'sent')
                                    update_account_timestamp(account_id)
                                    success_count += 1
                                    continue
                            
                        # Если всё равно ошибка, отмечаем как неудачную отправку
                        status = 'failed'
                        message_logger.debug(f"Recording failed message from account {account_id} to contact {contact_id}")
                        record_sent_message(account_id, contact_id, message_id, status)
                        
                        fail_count += 1
                        message_logger.error(f"Failed to send message from account {account_id} to contact {contact_id}: {error}")
                    
                    total_sent += 1

        # Завершаем работу прогресс-бара
        self.progress_bar.setValue(len(selected_contacts))
        self.progress_status.setText("Отправка завершена!")
        self.progress_details.setText(f"Отправлено: {success_count}, Ошибок: {fail_count}")
        self.progress_stats.setText(f"Всего контактов обработано: {len(selected_contacts)}")
        QApplication.processEvents()
        
        # Обновляем историю сообщений
        self.load_message_history()
        
        # После короткой паузы скрываем группу прогресса
        time.sleep(2)
        self.progress_group.hide()

        status_message = f"Успешно отправлено: {success_count}"
        if fail_count > 0:
            status_message += f", Ошибок: {fail_count}"

        QMessageBox.information(self, 'Результаты отправки', status_message)

        # Снимаем выделение с контактов и очищаем поле сообщения
        for checkbox in self.contact_checkboxes.values():
            checkbox.setChecked(False)

        self.message_input.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        init_database()

        self.client_manager = TelegramClientManager()

        for account in get_accounts():
            self.client_manager.add_account(account)
            if account.get('session_string'):
                self.client_manager.connect_client(account['id'])

        self.init_ui()

    def init_ui(self):
        # Основные настройки окна
        self.setWindowTitle('Telegram Multi-Account Message Sender')
        self.setGeometry(100, 100, 1200, 800)
        
        # Создаем вкладки с иконками и улучшенным стилем
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Стиль вкладок
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                margin-right: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
        """)

        # Создаем вкладки
        self.accounts_tab = AccountsTab(self.client_manager)
        self.contacts_tab = ContactsTab()
        self.messages_tab = MessagesTab(self.client_manager)
        
        # Глобальный стиль для кнопок
        self.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border: 1px solid #adadad;
            }
            QPushButton:pressed {
                background-color: #d4d4d4;
                border: 1px solid #8c8c8c;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox {
                padding: 5px;
            }
        """)

        # Добавляем вкладки с иконками
        self.tabs.addTab(self.accounts_tab, self.style().standardIcon(QStyle.SP_DialogOpenButton), 'Аккаунты')
        self.tabs.addTab(self.contacts_tab, self.style().standardIcon(QStyle.SP_FileDialogDetailedView), 'Контакты')
        self.tabs.addTab(self.messages_tab, self.style().standardIcon(QStyle.SP_MessageBoxInformation), 'Отправка сообщений')

        self.accounts_tab.accounts_changed.connect(self.on_accounts_changed)
        self.contacts_tab.contacts_changed.connect(self.on_contacts_changed)

    def on_accounts_changed(self):
        self.messages_tab.update_account_list()

    def on_contacts_changed(self):
        self.messages_tab.update_contact_list()

    def closeEvent(self, event):
        self.client_manager.disconnect_all()
        event.accept()

if __name__ == "__main__":
    os.makedirs('sessions', exist_ok=True)

    # Create and run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())