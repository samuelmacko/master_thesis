
from csv import writer
from datetime import date, datetime
from marshal import dump, load
from os import getenv
from pathlib import Path
from random import randrange
from typing import Any, List, Optional, Set, Tuple
from yaml import safe_load

from github import Github
from github.GithubException import (
    GithubException, RateLimitExceededException, UnknownObjectException
)

from .config import config_values
from .enums import EndCondition
from logger import logger_file_name, setup_logger
from .repository_data import RepositoryData
from .s3_handler import S3Handler
from .waiting import NoAPICalls, wait_for_api_calls


_GITHUB_ACCESS_TOKEN = getenv('GITHUB_ACCESS_TOKEN')

logger_config_values = config_values['logger']
logger = setup_logger(
    name=__name__, file=logger_config_values['file'],
    format=logger_config_values['format'], level=logger_config_values['level']
)


class Dataset:

    def __init__(self) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)

    @staticmethod
    def load_features(features_file: str) -> List[str]:
        with open(file=features_file, mode='r') as f:
            return safe_load(f)

    @staticmethod
    def prepare_csv(features: List[str], file_name: str) -> None:
        with open(file=file_name, mode='w') as f:
            csv_writer = writer(f, delimiter=',')
            csv_writer.writerow(features)

    @staticmethod
    def write_to_csv(data: List[Any], file_name: str) -> None:
        with open(file=file_name, mode='a') as f:
            csv_writer = writer(f, delimiter=',')
            data = [str(col) for col in data]
            csv_writer.writerow(data)

    @staticmethod
    def save_visited_ids(dat_file: str, ids_set: Set[int]) -> None:
        with open(file=dat_file, mode='wb') as f:
            dump(ids_set, f)

    @staticmethod
    def load_visited_ids(dat_file: str) -> Optional[Set[int]]:
        try:
            with open(file=dat_file, mode='rb') as f:
                try:
                    logger.debug(msg=f'IDs from file loaded: {dat_file}')
                    return load(f)
                except EOFError:
                    logger.debug(
                        msg=f'No IDs loaded: {dat_file}, created new set')
                    return set()
        except FileNotFoundError:
            logger.debug(msg=f'No IDs loaded: {dat_file}, created new set')
            return set()

    @staticmethod
    def id_generator(min_id: int, max_id: int) -> int:
        return randrange(min_id, max_id)

    def get_boundaries(self, from_date: date, to_date: date) -> (int, int):
        from_id = self._git.search_repositories(
            query=from_date.__str__()
        )[0].id
        to_id = self._git.search_repositories(
            query=to_date.__str__()
        )[0].id
        return from_id, to_id

    def save_all(self, file_set_tuples: List[Tuple[str, set]]) -> None:
        for tup in file_set_tuples:
            self.save_visited_ids(dat_file=tup[0], ids_set=tup[1])
        logger.info(msg='IDs saved to files')

    def upload_all(
        self, file_name_prefix: str, file_names: List[str], region_name: str
    ) -> None:
        s3_handler = S3Handler(region_name=region_name)
        if not s3_handler.bucket_exits_check():
            s3_handler.create_bucket()
            logger.info(msg='Created S3 bucket')

        for file_name in file_names:
            s3_handler.upload_file(
                file_name=file_name, prefix=file_name_prefix
            )
            s3_handler.delete_oldest_object(
                file_name=file_name, prefix=file_name_prefix
            )
        logger.info(msg='IDs files uploaded to the S3 bucket')

    def download_all(
        self, region_name: str, file_names: List[str],
        file_name_prefix: str = ''
    ) -> None:
        s3_handler = S3Handler(region_name=region_name)
        if s3_handler.bucket_exits_check():
            for file_name in file_names:
                s3_handler.download_file(
                    file_name=file_name, prefix=file_name_prefix
                )
            logger.info(msg='IDs files downloaded from S3 bucket')
        else:
            logger.info(msg='S3 bucket does not exist')

    def search_repos(
            self, from_year: str, to_year: str,
            unmaintained_ids_file: str, maintained_ids_file: str,
            not_suitable_ids_file: str,
            end_condition: EndCondition, value: int,
            region_name: str, file_name_prefix: str,
            partial_upload_size: int = 10
    ) -> None:
        self.download_all(
            file_names=[
                unmaintained_ids_file, maintained_ids_file,
                not_suitable_ids_file
            ], region_name=region_name, file_name_prefix=file_name_prefix
        )
        unmaintained_ids = self.load_visited_ids(
            dat_file=unmaintained_ids_file
        )
        maintained_ids = self.load_visited_ids(dat_file=maintained_ids_file)
        not_suitable_ids = self.load_visited_ids(
            dat_file=not_suitable_ids_file
        )

        from_year_date = datetime.strptime(from_year, '%Y').date()
        to_year_date = datetime.strptime(to_year, '%Y').date()

        maintained_count = len(maintained_ids)
        unmaintained_count = len(unmaintained_ids)

        repo_analyzed_counter = 0
        repo_data = RepositoryData(git=self._git)
        logger_file = logger_file_name(logger=logger)
        logger.info(msg='Start of the search')
        try:
            while len(eval(EndCondition[end_condition].value)) < value:
                try:
                    while True:
                        from_id, to_id = self.get_boundaries(
                            from_date=from_year_date, to_date=to_year_date
                        )
                        generated_id = self.id_generator(
                            min_id=from_id, max_id=to_id
                        )
                        if (
                                generated_id not in unmaintained_ids and
                                generated_id not in maintained_ids and
                                generated_id not in not_suitable_ids
                        ):
                            break

                    repo = self._git.get_repo(full_name_or_id=generated_id)
                    repo_data.set_repo(repo=repo)

                    if repo_data.suitable():
                        if repo_data.unmaintained():
                            unmaintained_ids.add(generated_id)
                            unmaintained_count += 1
                            logger.info(
                                msg='Added unmaintained repo ID: ' +
                                    f'{generated_id}, ' +
                                    f'rank: {unmaintained_count}'
                            )
                        else:
                            maintained_ids.add(generated_id)
                            maintained_count += 1
                            logger.info(
                                msg='Added maintained repo ID: ' +
                                    f'{generated_id}, ' +
                                    f'rank: {maintained_count}'
                            )
                    else:
                        not_suitable_ids.add(generated_id)
                        logger.info(
                            msg=f'Added not suitable repo ID: {generated_id}'
                        )
                    repo_analyzed_counter += 1
                    if repo_analyzed_counter == partial_upload_size:
                        repo_analyzed_counter = 0
                        logger.info(msg='Partial save and upload')
                        self.save_all(
                            file_set_tuples=[
                                (unmaintained_ids_file, unmaintained_ids),
                                (maintained_ids_file, maintained_ids),
                                (not_suitable_ids_file, not_suitable_ids)
                            ]
                        )
                        self.upload_all(
                            file_names=[
                                unmaintained_ids_file, maintained_ids_file,
                                not_suitable_ids_file, logger_file
                            ],
                            region_name=region_name,
                            file_name_prefix=file_name_prefix
                        )

                except RateLimitExceededException:
                    logger.info(msg='Github API rate limit reached')
                    wait_for_api_calls(git=self._git)
                    continue
                except UnknownObjectException:
                    not_suitable_ids.add(generated_id)
                    logger.info(
                        msg=f'Added not suitable repo ID: {generated_id}'
                    )
                    continue
                except GithubException:
                    logger.info(msg='Encoutered an incomplete repository')
                    continue
                except NoAPICalls:
                    logger.info(msg='API calls were not granted')
                    return

        finally:
            self.save_all(
                file_set_tuples=[
                    (unmaintained_ids_file, unmaintained_ids),
                    (maintained_ids_file, maintained_ids),
                    (not_suitable_ids_file, not_suitable_ids)
                ]
            )
            self.upload_all(
                file_names=[
                    unmaintained_ids_file, maintained_ids_file,
                    not_suitable_ids_file, logger_file
                ],
                region_name=region_name, file_name_prefix=file_name_prefix
            )
            logger.info(msg='End of the search')

    def compute_features(
            self, features_file: str, ids_file_name: str, csv_file_name: str,
            region_name: str, file_name_prefix: str,
            partial_upload_size: int = 10
    ) -> None:
        try:
            self.download_all(
                file_names=[ids_file_name, csv_file_name],
                region_name=region_name, file_name_prefix=file_name_prefix
            )

            repo_data = RepositoryData(git=self._git)
            features = self.load_features(features_file=features_file)
            repo_computed_counter = 0
            computed_ids = set()

            if not Path(csv_file_name).is_file():
                self.prepare_csv(features=features, file_name=csv_file_name)

            repo_ids = self.load_visited_ids(dat_file=ids_file_name)
            logger.debug(msg=f'IDs set size: {len(repo_ids)}')

            ids_all = len(repo_ids)
            ids_count = 0

            logger_file = logger_file_name(logger=logger)
            logger.info(msg='Start of computation')
            for repo_id in repo_ids:
                try:
                    logger.info(msg=f'Computing repo: {repo_id}')
                    repo_data.set_repo(repo_name_or_id=repo_id)
                    self.write_to_csv(
                        data=repo_data.get_row(features=features),
                        file_name=csv_file_name
                    )
                    ids_count += 1
                    logger.info(
                        msg=f'Computed repo: {repo_id} to: {csv_file_name}, ' +
                            f'rank: {ids_count} / {ids_all}'
                    )
                    repo_computed_counter += 1
                    computed_ids.add(repo_id)

                    if repo_computed_counter == partial_upload_size:
                        repo_computed_counter = 0
                        logger.info(msg='Partial upload')
                        self.upload_all(
                            file_names=[csv_file_name, logger_file],
                            region_name=region_name,
                            file_name_prefix=file_name_prefix
                        )
                except RateLimitExceededException:
                    logger.info(msg='Github API rate limit reached')
                    wait_for_api_calls(git=self._git)
                    continue
                except UnknownObjectException:
                    logger.info(msg='Encountered a removed repository')
                    continue
                except NoAPICalls:
                    logger.info(msg='API calls were not granted')
                    return

        finally:
            remaining_ids = repo_ids - computed_ids
            self.save_all(file_set_tuples=[(ids_file_name, remaining_ids)])
            self.upload_all(
                file_names=[csv_file_name, ids_file_name, logger_file],
                region_name=region_name, file_name_prefix=file_name_prefix
            )
            logger.info(msg='End of the search')
