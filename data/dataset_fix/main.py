
from csv import reader as csv_reader, writer as csv_writer
from typing import List

from data_gathering import GIT_INSTANCE
from data_gathering.logger import setup_logger
from data_gathering.repository_data import RepositoryData
from data_gathering.waiting import NoAPICalls, wait_for_api_calls

from github import (
    GithubException, RateLimitExceededException, UnknownObjectException
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


rd = RepositoryData(git=GIT_INSTANCE)

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
        for i, row in enumerate(matrix[1:]):
            try:
                row_counter += 1
                logger.debug(
                    msg=f'Started computing row: {row_counter} / {rows_count}'
                )

                rd.set_repo(repo_name_or_id=row[0])

                row[6] = rd.commits_count()
                row[7] = rd.branches_count()
                row[15] = rd.avg_dev_account_age()
                row[23] = rd.devs_followers_avg()
                row[24] = rd.devs_following_avg()

                matrix_updated.append(row)
                del matrix[1]

                if i % 10 == 0:
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
