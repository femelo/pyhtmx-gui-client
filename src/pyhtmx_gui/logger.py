import logging
from typing import Union
from colorlog import ColoredFormatter
from .config import config_data


def init_logger(
    name: str,
    level: Union[int, str] = logging.DEBUG,
) -> logging.Logger:
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a console handler and set the log level to DEBUG
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Create a formatter with colors
    formatter = ColoredFormatter(
        fmt=(
            "%(log_color)s[%(levelname)-8s] "
            "[%(asctime)s.%(msecs)03d] [%(filename)-15s @ L%(lineno)03d] "
            "%(message)s%(reset)s"
        ),
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'light_green',
            'WARNING':  'yellow',
            'ERROR':    'light_red',
            'CRITICAL': 'red',
        },
    )

    # Add the formatter to the console handler
    ch.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(ch)

    return logger


logger: logging.Logger = init_logger(
    "PYHTMX GUI",
    level=config_data["log-level"].upper(),
)
