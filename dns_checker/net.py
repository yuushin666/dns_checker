import asyncio
import ipaddress
import subprocess
from pathlib import Path

from .config import WATCHDOG
from .utils import get_logger, get_status_str

logger = get_logger(__name__)


async def shell_exec(command: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=WATCHDOG)
        result = (
            proc.returncode if proc.returncode is not None else 124,
            out.decode(errors='replace'),
            err.decode(errors='replace'),
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        result = (124, '', 'killed: watchdog timeout')

    logger.debug(result)
    return result


def find_iface_by_subnet(prefix: str) -> str:
    wanted = ipaddress.ip_network(prefix, strict=False)
    for iface in Path('/sys/class/net').iterdir():
        out = subprocess.run(
            ['ip', '-o', '-4', 'addr', 'show', 'dev', iface.name],
            capture_output=True, text=True).stdout
        for line in out.splitlines():
            addr = line.split()[3].split('/')[0]
            if ipaddress.ip_address(addr) in wanted:
                return iface.name
    return '-'


async def get_iface_status(iface: str) -> bool:
    code, out, _ = await shell_exec(f'ip -o link show dev {iface} | grep UP')
    status = code == 0
    logger.debug(f'interface {iface} is {get_status_str(status)}')
    return status


async def set_iface(iface: str, new_status: str) -> None:
    await shell_exec(f'ip link set {iface} {new_status}')
    logger.info(f'interface {iface} set to {new_status}')
