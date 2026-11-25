import os
import sys

from aiohttp import ClientTimeout


def require_env(name: str, default: str | None = None) -> str:
    """Возвращает значение переменной или завершает программу."""
    value = os.getenv(name) or default
    if not value:
        print(
            f'Отсутствует переменная окружения {name}. '
            'Программа принудительно остановлена.'
        )
        sys.exit(1)
    return value


SYNC_SEC = int(require_env('SYNC_SEC', '10'))
RETRY_PERIOD = int(require_env('RETRY_PERIOD', '60'))
WATCHDOG = int(require_env('WATCHDOG', '25'))
TIMEOUT = ClientTimeout(float(require_env('TIMEOUT', '15')))

DOMAINS = [d for d in require_env('DOMAINS').split(',') if d.strip()]
SERVER = require_env('SERVER')
SVC_NET = os.getenv('SVC_NET', '')

PHONES = [p for p in require_env('PHONES').split(',') if p.strip()]
SMS_URL = require_env('SMS_URL')
TG_PROXY = require_env('TG_PROXY')
BOT_ID = require_env('BOT_ID')
CHAT_ID = require_env('CHAT_ID')
