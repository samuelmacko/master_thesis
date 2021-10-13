
from datetime import datetime
from logging import Logger
from time import sleep

from github import Github

from data_gathering import GIT_INSTANCE, GIT_INSTANCE_PETIN


class NoAPICalls(Exception):
    pass


def wait_for_api_calls(
    logger: Logger, number_of_attempts: int = 3
) -> Github:

    for i in range(number_of_attempts):

        if GIT_INSTANCE.get_rate_limit().core.remaining > 0:
            git = GIT_INSTANCE
        elif GIT_INSTANCE_PETIN.get_rate_limit().core.remaining > 0:
            git = GIT_INSTANCE_PETIN
        else:
            if GIT_INSTANCE.rate_limiting_resettime < GIT_INSTANCE_PETIN.rate_limiting_resettime:
                git = GIT_INSTANCE
            else:
                git = GIT_INSTANCE

        waiting_time = time_to_wait(timestamp=git.rate_limiting_resettime) + 60

        if waiting_time > 1800:
            waiting_time = 1800

        logger.info(msg=f'Waiting for {waiting_time / 60} minutes')
        sleep(waiting_time)

        api_calls = git.get_rate_limit().core.remaining
        if api_calls > 0:
            logger.debug(msg=f'Available {api_calls} API calls')
            return git
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
