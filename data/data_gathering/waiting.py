
from datetime import datetime
from logging import Logger
from time import sleep

from github import Github

from data_gathering import GITHUB_INSTANCES


class NoAPICalls(Exception):
    pass


def wait_for_api_calls(
    logger: Logger, number_of_attempts: int = 3
) -> Github:

    for i in range(number_of_attempts):

        remaining_calls = [
            g.get_rate_limit().core.remaining for g in GITHUB_INSTANCES
        ]
        max_calls = max(remaining_calls)

        if max_calls > 0:
            max_calls_index = remaining_calls.index(max_calls)
            git = GITHUB_INSTANCES[max_calls_index]
            logger.debug(msg=f'Using GIT_INSTANCE {max_calls_index} : >calls')

            return git
        else:
            remaining_times = [
                g.rate_limiting_resettime for g in GITHUB_INSTANCES
            ]
            min_reset = min(remaining_time)
            min_reset_index = remaining_times.index(min_reset)

            git = GITHUB_INSTANCES[min_reset_index]
            logger.debug(msg=f'Using GIT_INSTANCE {min_reset_index} : <time')

        waiting_time = time_to_wait(timestamp=git.rate_limiting_resettime) + 60

        if waiting_time > 300:
            waiting_time = 300

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
