
import asyncio
import datetime
import sys
import time

from .checker import check_dns
from .config import RETRY_PERIOD, SERVER, SVC_NET, SYNC_SEC
from .net import find_iface_by_subnet, get_iface_status, set_iface
from .notify import send_report
from .utils import get_logger, get_status_str, setup_logging

logger = get_logger('main')
IFACE = find_iface_by_subnet(SVC_NET) if SVC_NET else '-'


async def main(server: str, prev: bool | None) -> bool:
    """Возвращает текущий статус и уведомляет об изменении."""
    status = await check_dns(server)
    if prev and status != prev:
        new_status = get_status_str(status)
        logger.info(f'DNS {server}: {get_status_str(prev)} -> {new_status}')
        if IFACE != '-':
            iface_status = await get_iface_status(IFACE)
            if iface_status != status:
                await set_iface(IFACE, new_status)
        await send_report(f'Test: DNS {server} is {new_status}')
    return status


async def wait_for_sync() -> None:
    """Дожидается ближайшей границы Ч:М:SYNC_SEC."""
    now = datetime.datetime.now()
    target = now.replace(second=SYNC_SEC, microsecond=0)
    if target <= now:
        target += datetime.timedelta(seconds=RETRY_PERIOD)
    delay = (target - now).total_seconds()
    logger.debug(f'Первый проход в {target:%H:%M:%S}, ждём {delay:.1f} с')
    await asyncio.sleep(delay)


async def main_loop() -> None:
    await wait_for_sync()
    prev: bool | None = await get_iface_status(IFACE) if IFACE != '-' else None
    next_run = time.monotonic()
    while True:
        try:
            prev = await main(SERVER, prev)
        except Exception:
            logger.exception('Проход завершился с ошибкой')
        next_run += RETRY_PERIOD
        await asyncio.sleep(max(0.0, next_run - time.monotonic()))


if __name__ == '__main__':
    setup_logging(debug=True)

    try:
        asyncio.run(main_loop())

    except KeyboardInterrupt:
        logger.info('Программа остановлена Ctrl+C.')

    except Exception as error:
        logger.error(f'Сбой: {error}')
        sys.exit(1)
