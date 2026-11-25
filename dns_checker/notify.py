import asyncio
from http import HTTPStatus
from random import sample

from aiohttp import ClientSession

from config import BOT_ID, CHAT_ID, PHONES, SMS_URL, TG_PROXY, TIMEOUT
from net import shell_exec
from utils import get_logger

logger = get_logger(__name__)


async def send_request(
        session: ClientSession, url: str, payload: dict, report_type: str
) -> None:
    try:
        async with session.post(url, json=payload) as response:
            if response.status != HTTPStatus.OK:
                error = f'Вернулся статус {response.status}'
                body = await response.text()
                logger.debug(f'{error}: {body[:50].replace(chr(10), " ")}')
                raise Exception(error)
        logger.info(f'Успешная отправка {report_type} ({payload})')

    except Exception as error:
        logger.error(f'Сбой отправки {report_type}: {error}')


async def send_sms(session: ClientSession, text: str) -> None:
    sms_data = {
        'message': text,
        'phones': sample(PHONES, len(PHONES))
    }
    await send_request(session, SMS_URL, sms_data, 'СМС')


async def send_tg(session: ClientSession, text: str) -> None:
    await shell_exec(f'nslookup {TG_PROXY}')
    tg_data = {
        'parse_mode': 'html',
        'chat_id': CHAT_ID,
        'text': text
    }
    await send_request(
        session, f'https://{TG_PROXY}/{BOT_ID}/sendMessage', tg_data, 'TG')


async def send_report(text: str) -> None:
    async with ClientSession(timeout=TIMEOUT) as session:
        await asyncio.gather(
            send_sms(session, text),
            send_tg(session, text),
        )
