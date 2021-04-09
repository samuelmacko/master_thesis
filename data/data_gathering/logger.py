
import logging
from os.path import basename


def setup_logger(
    name: str, file: str, format: str, level: str = 'INFO'
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    converted_level = logging.getLevelName(level)
    file_handler = logging.FileHandler(file)
    file_handler.setLevel(converted_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(converted_level)

    formatter = logging.Formatter(format)
    file_handler.setFormatter(fmt=formatter)
    console_handler.setFormatter(fmt=formatter)

    logger.addHandler(hdlr=file_handler)
    logger.addHandler(hdlr=console_handler)

    return logger


def logger_file_name(logger: logging.Logger) -> str:
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return basename(handler.baseFilename)
    return ''
