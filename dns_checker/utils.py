import logging
import sys


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name.split('.')[-1])


def setup_logging(debug=False) -> None:
    """Настраивает логирование с выводом в `sys.stdout`.
    По умолчанию уровень `INFO`, `debug=True` включает `DEBUG`.
    """
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stdout,
    )


def get_status_str(status: bool | None) -> str:
    match status:
        case None:
            return 'n/a'
        case True:
            return 'up'
        case False:
            return 'down'


def oneline(text: str) -> str:
    """Схлопывает переводы строк и табы в одиночные пробелы."""
    return ' '.join(text.split())
