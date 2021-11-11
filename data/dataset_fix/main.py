
from csv import reader as csv_reader, writer as csv_writer
from typing import List

from data_gathering.logger import setup_logger
from data_gathering.repository_data import RepositoryData
from data_gathering.waiting import get_git_instance, NoAPICalls

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


COMMIT_LAST_MODIFIED_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

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

        git = get_git_instance(number_of_attempts=10, logger=logger)
        rd = RepositoryData(git=git)

    try:
        for row in matrix[1:]:
            try:
                row_counter += 1
                logger.info(
                    msg=f'Started computing repository: {row[0]}, row: {row_counter} / {rows_count}'
                )

                if row[26] == 'ph':
                    rd.set_repo(repo_name_or_id=row[0])

                    logger.debug(msg='Computing magnetism')
                    matrix[1][26] = rd.magnetism()
                    logger.debug(msg='Computing stickiness')
                    matrix[1][27] = rd.stickiness()

                matrix_updated.append(matrix[1])

                del matrix[1]

                if row_counter % 10 == 0:
                    logger.info(msg='Saving files')
                    save_all()
                    matrix_updated = []

            except RateLimitExceededException:
                logger.info(msg='Github API rate limit reached')
                git = get_git_instance(number_of_attempts=10, logger=logger)
                rd = RepositoryData(git=git)
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
