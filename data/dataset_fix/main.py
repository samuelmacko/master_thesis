
from csv import reader as csv_reader, writer as csv_writer
from typing import List, Tuple

from data_gathering import GIT_INSTANCE
from data_gathering.logger import setup_logger
from data_gathering.waiting import NoAPICalls, wait_for_api_calls

from github import (
    Github, GithubException, RateLimitExceededException, UnknownObjectException
)


def save_matrix(
        file_name: str, matrix: List[List], append: bool = False
) -> None:
    if append:
        open_type = 'a'
    else:
        open_type = 'w'

    with open(file_name, open_type, newline='') as output_csv_file:
        writer = csv_writer(output_csv_file, delimiter=',')
        writer.writerows(matrix)


def save_all() -> None:
    save_matrix(
        file_name=f'dataset_fix/dataset/{dataset}_updated.csv',
        matrix=matrix_updated, append=True
    )
    save_matrix(
        file_name=f'dataset_fix/dataset/{dataset}.csv',
        matrix=matrix
    )


def suitable(git: Github, repo_name: str) -> Tuple[int, bool]:
    if 'dotfile' in repo_name:
        return 1, False

    repo = git.get_repo(full_name_or_id=repo_name)

    if len(list(repo.get_commits())) < 20:
        return 2, False
    elif len(list(repo.get_contributors())) < 3:
        return 3, False

    return 0, True


not_suitable_counter = {
    'dotfile': 0,
    'commits': 0,
    'contributors': 0,
}

logger = setup_logger(
    name=__name__, file='dataset_fix/dataset_fix.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level='DEBUG'
)

datasets = ['maintained', 'unmaintained']
for dataset in datasets:
    logger.info(msg=f'Started computing {dataset} dataset')

    with open(
        f'dataset_fix/dataset/{dataset}.csv', newline=''
    ) as input_csv_file:
        reader = csv_reader(input_csv_file, delimiter=',')
        matrix = list(reader)
        matrix_updated = []

        rows_count = len(matrix)
        row_counter = 0

    try:
        for row in matrix[1:]:
            try:
                row_counter += 1
                logger.info(
                    msg=f'Started computing repository: {row[0]}, row: {row_counter} / {rows_count}'
                )

                code, suit = suitable(git=GIT_INSTANCE, repo_name=row[0])
                if suit:
                    matrix_updated.append(row)
                else:
                    if code == 1:
                        not_suitable_counter['dotfile'] += 1
                    elif code == 2:
                        not_suitable_counter['commits'] += 1
                    elif code == 3:
                        not_suitable_counter['contributors'] += 1

                    logger.info(
                        msg=f'Repository: {row[0]} is not suitable {not_suitable_counter}'
                    )

                del matrix[1]

                if row_counter % 10 == 0:
                    logger.info(msg='Saving files')
                    save_all()
                    matrix_updated = []

            except RateLimitExceededException:
                logger.info(msg='Github API rate limit reached')
                wait_for_api_calls(
                    git=GIT_INSTANCE, number_of_attempts=10, logger=logger
                )
                continue
            except UnknownObjectException:
                logger.debug(msg='Unknown object')
                continue
            except GithubException:
                logger.debug(msg='Github exception')
                continue
            except NoAPICalls:
                logger.info(msg='API calls were not granted')
                break

    finally:
        logger.info(msg='Saving files')
        save_all()
