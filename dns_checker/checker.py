import asyncio
from random import sample

from .config import DOMAINS
from .net import shell_exec
from .utils import get_logger, get_status_str, oneline

logger = get_logger(__name__)


async def nslookup(domain: str, server: str) -> None:
    code, out, err = await shell_exec(
        f'nslookup -timeout=5 -retry=3 {domain} {server}')
    if code == 0 and 'timed out' in out.lower():
        logger.warning(f'{server}: first attempt timed out for {domain}')
    if code != 0:
        raise Exception(oneline(out.strip() or err.strip() or 'no output'))


async def check_dns(server: str) -> bool:
    domains = sample(DOMAINS, len(DOMAINS))
    tasks = [
        asyncio.create_task(nslookup(domain, server))
        for domain in domains
    ]
    for task in tasks:
        await asyncio.sleep(0.1)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    resolved: list[str] = []
    failed: list[str] = []

    for domain, res in zip(domains, results):
        if isinstance(res, Exception):
            logger.error(f'Сбой {domain}: {oneline(str(res))}')
            failed.append(domain)
        else:
            resolved.append(domain)

    status = bool(resolved)
    logger.info(
        f'resolved: {resolved}, failed: {failed}, '
        f'{len(resolved)}:{len(failed)}, server is {get_status_str(status)}'
    )
    return status
