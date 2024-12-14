import logging
from typing import Union
from colorlog import ColoredFormatter


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
        fmt="%(log_color)s[%(name)s : %(levelname)-8s] %(message)s%(reset)s",
        datefmt=None,
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

logger = init_logger("PYHTMX GUI", level=logging.DEBUG)
