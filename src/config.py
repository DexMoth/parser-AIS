import json
import os
from pathlib import Path

# путь к файлу конфигурации
CONFIG_FILE = Path(__file__).parent.parent / 'config.json'

# значения по умолчанию
DEFAULT_CONFIG = {
    'USE_LOGIN_FROM_CONFIG': True,
    'LOGIN_DATA': {'login': '', 'password': ''},
    'DELAY_MIN': 40,
    'DELAY_MAX': 60,
    'TIMEOUT': 30,
    'BASE_URL': 'https://www.elibrary.ru'
}

# чтение конфигурации из json
config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"ошибка чтения config.json: {e}")

# настройки авторизации
USE_LOGIN_FROM_CONFIG = config.get('USE_LOGIN_FROM_CONFIG', DEFAULT_CONFIG['USE_LOGIN_FROM_CONFIG'])
"""
True: при авторизации используется логин и пароль из LOGIN_DATA в config.json
False: перед авторизацией пользователю необходимо ввести логин и пароль в консоли
"""

LOGIN_DATA = config.get('LOGIN_DATA', DEFAULT_CONFIG['LOGIN_DATA'])

# настройки задержек
DELAY_MIN = config.get('DELAY_MIN', DEFAULT_CONFIG['DELAY_MIN'])
DELAY_MAX = config.get('DELAY_MAX', DEFAULT_CONFIG['DELAY_MAX'])

# таймаут запроса
TIMEOUT = config.get('TIMEOUT', DEFAULT_CONFIG['TIMEOUT'])

BASE_URL = config.get('BASE_URL', DEFAULT_CONFIG['BASE_URL'])
