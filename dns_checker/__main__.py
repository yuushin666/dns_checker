
import asyncio
from collections import deque
import datetime
import sys
import time

from .checker import check_dns
from .config import RETRY_PERIOD, SERVER, SVC_NET, SYNC_SEC
from .net import find_iface_by_subnet, set_iface
from .notify import send_report
from .utils import get_logger, get_status_str, setup_logging

logger = get_logger('main')
IFACE = find_iface_by_subnet(SVC_NET) if SVC_NET else '-'
HISTORY_SIZE = 2
history: deque[bool] = deque(maxlen=HISTORY_SIZE)


async def wait_for_sync() -> None:
    """Дожидается ближайшей границы Ч:М:SYNC_SEC."""
    now = datetime.datetime.now()
    target = now.replace(second=SYNC_SEC, microsecond=0)
    if target <= now:
        target += datetime.timedelta(seconds=RETRY_PERIOD)
    delay = (target - now).total_seconds()
    logger.debug(f'First pass at {target:%H:%M:%S}, waiting {delay:.1f} s')
    await asyncio.sleep(delay)


async def main(server: str, prev: bool | None) -> bool | None:
    """Подтверждает статус, если он совпадает с последним результатом и
    отличается от предпоследнего (или это первая установленная база),
    а также и уведомляет об изменении.
    """
    current = await check_dns(server)

    confirmed = prev
    if len(history) == 2:
        older, newer = history
        if current == newer and (current != older or prev is None):
            confirmed = current
        logger.debug(
            f'older: {older}, newer: {newer}, current: {current}, '
            f'confirmed: {confirmed}, prev: {prev}'
        )

    history.append(current)

    if prev is not None and confirmed != prev:
        new_status = get_status_str(confirmed)
        logger.info(
            f'confirmed status: {get_status_str(prev)} -> {new_status}'
        )
        if IFACE != '-' and confirmed is not None:
            await set_iface(IFACE, confirmed)
        await send_report(f'DNS {server} is {new_status}')

    return confirmed


async def main_loop() -> None:
    await wait_for_sync()
    prev_status: bool | None = None
    next_run = time.monotonic()
    while True:
        try:
            prev_status = await main(SERVER, prev_status)
        except Exception:
            logger.exception('Pass finished with error')
        next_run += RETRY_PERIOD
        await asyncio.sleep(max(0.0, next_run - time.monotonic()))


if __name__ == '__main__':
    setup_logging(debug=True)

    try:
        asyncio.run(main_loop())

    except KeyboardInterrupt:
        logger.info('Stopped by Ctrl+C.')

    except Exception as error:
        logger.error(f'Unexpected error: {error}')
        sys.exit(1)
