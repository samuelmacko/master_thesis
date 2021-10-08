
from datetime import datetime
from logging import Logger
from time import sleep

from github import Github


class NoAPICalls(Exception):
    pass


def wait_for_api_calls(
    git: Github, logger: Logger, number_of_attempts: int = 3
) -> None:
    for i in range(number_of_attempts):
        waiting_time = time_to_wait(timestamp=git.rate_limiting_resettime) + 30

        if waiting_time > 3000:
            waiting_time = 3000

        logger.info(msg=f'Waiting for {waiting_time / 60} minutes')
        sleep(waiting_time)

        api_calls = git.get_rate_limit().core.remaining
        if api_calls > 0:
            logger.debug(msg=f'Available {api_calls} API calls')
            return
        else:
            logger.debug(
                msg=f'No API calls received in attempt {i} /' +
                f'{number_of_attempts}'
            )

    raise NoAPICalls('No API calls received')


def time_to_wait(timestamp: int) -> int:
    current_datetime = datetime.now()
    datetime_to_reset = datetime.fromtimestamp(timestamp)
    return (datetime_to_reset - current_datetime).seconds
