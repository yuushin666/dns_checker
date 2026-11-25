import asyncio
from random import sample

from .config import DOMAINS
from .net import shell_exec
from .utils import get_logger, get_status_str, oneline

logger = get_logger(__name__)

CONFIRM_DELAY = 5


async def nslookup(domain: str, server: str, delay: int = 0) -> None:
    await asyncio.sleep(delay)
    code, out, err = await shell_exec(
        f'nslookup -type=A -timeout=5 -retry=3 {domain} {server}')
    timeouts = out.lower().count('timed out')
    if timeouts:
        logger.warning(f'{server}: {timeouts} timed out attempts for {domain}')
    if code != 0:
        raise Exception(oneline(out.strip() or err.strip() or 'no output'))


async def probe(server: str) -> bool:
    domains = sample(DOMAINS, len(DOMAINS))
    tasks = [
        asyncio.create_task(nslookup(domain, server, i))
        for i, domain in enumerate(domains)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    resolved: list[str] = []
    failed: list[str] = []

    for domain, res in zip(domains, results):
        if isinstance(res, Exception):
            logger.error(f'NS lookup failed for {domain}: {oneline(str(res))}')
            failed.append(domain)
        else:
            resolved.append(domain)

    status = bool(resolved)
    logger.info(
        f'resolved: {resolved}, failed: {failed}, '
        f'{len(resolved)}:{len(failed)}, server is {get_status_str(status)}'
    )
    return status


async def check_dns(server: str) -> bool:
    status = await probe(server)
    if not status:
        logger.warning(
            f'{server}: probe failed, confirming in {CONFIRM_DELAY}s'
        )
        await asyncio.sleep(CONFIRM_DELAY)
        status = await probe(server)
        if status:
            logger.info(f'{server}: recovered on confirmation probe')
    return status
