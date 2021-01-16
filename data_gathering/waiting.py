
from datetime import datetime
from time import sleep

from github import Github

from data_gathering import logger_config_values
from logger import setup_logger


logger = setup_logger(
    name=__name__, file=logger_config_values['file'],
    format=logger_config_values['format'], level=logger_config_values['level']
)


class NoAPICalls(Exception):
    pass


def wait_for_api_calls(git: Github, number_of_attempts: int = 3) -> None:
    for i in range(number_of_attempts):
        waiting_time = time_to_wait(timestamp=git.rate_limiting_resettime) + 30
        logger.info(msg=f'Waiting for {waiting_time} seconds')
        sleep(waiting_time)

        api_calls = git.get_rate_limit().core.remaining
        if api_calls > 0:
            logger.debug(msg=f'Available {api_calls} API calls')
            return
        else:
            logger.debug(
                msg=f'No API calls received in attempt {i} /' +
                '{number_of_attempts}'
            )

    raise NoAPICalls('No API calls received')


def time_to_wait(timestamp: int) -> int:
    current_datetime = datetime.now()
    datetime_to_reset = datetime.fromtimestamp(timestamp)
    return (datetime_to_reset - current_datetime).seconds
