
from csv import writer
from datetime import date, datetime, timedelta
from logging import getLogger, Logger
from marshal import dump, load
from pathlib import Path
from random import randrange, sample
from requests.exceptions import ConnectionError, ReadTimeout
from time import sleep
from typing import Any, List, Optional, Set, Tuple
from yaml import safe_load

from github import Github
from github.GithubException import (
    GithubException, RateLimitExceededException, UnknownObjectException
)

from data_gathering import logger_config_values
from .enums import EndCondition
from .logger import logger_file_name, setup_logger
from .repository_data import RepositoryData
from .s3_handler import S3Handler
from .waiting import get_git_instance, NoAPICalls


class Dataset:

    def __init__(self) -> None:
        self._git: Github = get_git_instance()

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
    def load_visited_ids(
            dat_file: str, logger: Optional[Logger] = None
    ) -> Optional[Set[int]]:
        if not logger:
            logger = getLogger('dummy')

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
    def random_date(from_date: date, to_date: date) -> date:
        delta = to_date - from_date
        offset_day = randrange(delta.days)
        return from_date + timedelta(days=offset_day)

    def get_random_repos_ids(
            self, query: str, n: Optional[int] = None
    ) -> List[int]:
        repos = list(self._git.search_repositories(query=query))

        if n:
            return [repo.id for repo in sample(repos, n)]
        else:
            return [repo.id for repo in repos]

    def save_all(
        self, file_set_tuples: List[Tuple[str, set]], logger: Logger
    ) -> None:
        for tup in file_set_tuples:
            self.save_visited_ids(dat_file=tup[0], ids_set=tup[1])
        logger.info(msg='IDs saved to files')

    @staticmethod
    def upload_all(
        file_name_prefix: str, file_names: List[str], region_name: str,
        logger: Logger
    ) -> None:
        s3_handler = S3Handler(region_name=region_name)
        if not s3_handler.bucket_exits_check():
            s3_handler.create_bucket()
            logger.info(msg='Created S3 bucket')

        for file_name in file_names:
            s3_handler.upload_file(
                file_name=file_name, prefix=file_name_prefix, logger=logger
            )
            s3_handler.delete_oldest_object(
                file_name=file_name, prefix=file_name_prefix, logger=logger
            )
        logger.info(msg='IDs files uploaded to the S3 bucket')

    def save_and_upload_all(
            self, file_set_tuples: List[Tuple[str, set]],
            other_files: Optional[List[str]], logger: Logger,
            region_name: str, file_name_prefix: str
    ) -> None:
        file_names = [file_name[0] for file_name in file_set_tuples]
        if other_files:
            file_names += other_files

        self.save_all(file_set_tuples=file_set_tuples, logger=logger)
        self.upload_all(
            file_name_prefix=file_name_prefix, file_names=file_names,
            region_name=region_name, logger=logger
        )

    @staticmethod
    def already_visited(
            repo_id: int, id_sets: Optional[List[Set[int]]] = None
    ) -> bool:
        try:
            for id_set in id_sets:
                if repo_id in id_set:
                    return True
            return False

        except TypeError:
            return False

    @staticmethod
    def download_all(
        region_name: str, file_names: List[str], logger: Logger,
        file_name_prefix: str = ''
    ) -> None:
        s3_handler = S3Handler(region_name=region_name)
        if s3_handler.bucket_exits_check():
            for file_name in file_names:
                s3_handler.download_file(
                    file_name=file_name, prefix=file_name_prefix, logger=logger
                )
            logger.info(msg='IDs files downloaded from S3 bucket')
        else:
            logger.info(msg='S3 bucket does not exist')

    def search_repos(
            self, logger_name: str, from_year: str, to_year: str,
            unmaintained_ids_file: str, maintained_ids_file: str,
            not_suitable_ids_file: str,
            end_condition: EndCondition, value: int,
            region_name: str, file_name_prefix: str, query: str,
            partial_upload_size: int = 10
    ) -> None:
        logger = setup_logger(
            name=__name__, file=logger_name,
            format=logger_config_values['format'],
            level=logger_config_values['level']
        )
        self.download_all(
            file_names=[
                unmaintained_ids_file, maintained_ids_file,
                not_suitable_ids_file
            ], region_name=region_name, file_name_prefix=file_name_prefix,
            logger=logger
        )
        unmaintained_ids = self.load_visited_ids(
            dat_file=unmaintained_ids_file, logger=logger
        )
        maintained_ids = self.load_visited_ids(
            dat_file=maintained_ids_file, logger=logger
        )
        not_suitable_ids = self.load_visited_ids(
            dat_file=not_suitable_ids_file, logger=logger
        )

        main_names = self.load_visited_ids(
            dat_file='main_names.dat', logger=logger
        )

        file_set_tuples = [
            (unmaintained_ids_file, unmaintained_ids),
            (maintained_ids_file, maintained_ids),
            (not_suitable_ids_file, not_suitable_ids),
            ('main_names.dat', main_names)
        ]

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
                    random_date = self.random_date(
                        from_date=from_year_date,
                        to_date=to_year_date
                    )
                    logger.debug(msg=f'random date: {random_date}')
                    repos_ids = self.get_random_repos_ids(
                        query=query.format(date=random_date), n=100
                    )

                    for repo_id in repos_ids:

                        repo = self._git.get_repo(full_name_or_id=repo_id)
                        repo_data.set_repo(repo=repo)

                        if (repo_name := repo.name) in main_names:
                            continue

                        if repo_data.suitable():
                            if repo_data.unmaintained():
                                unmaintained_ids.add(repo_id)
                                unmaintained_count += 1
                                logger.info(
                                    msg='Added unmaintained repo ID: ' +
                                        f'{repo_id}, ' +
                                        f'rank: {unmaintained_count}'
                                )
                            else:
                                maintained_ids.add(repo_id)
                                main_names.add(repo_name)
                                maintained_count += 1
                                logger.info(
                                    msg='Added maintained repo name: ' +
                                        f'{repo_name}, ' +
                                        f'rank: {maintained_count}'
                                )
                        else:
                            not_suitable_ids.add(repo_id)
                            logger.info(
                                msg=f'Added not suitable repo ID: {repo_id}'
                            )
                        repo_analyzed_counter += 1
                        if repo_analyzed_counter == partial_upload_size:
                            repo_analyzed_counter = 0
                            logger.info(msg='Partial save and upload')
                            self.save_and_upload_all(
                                file_set_tuples=file_set_tuples,
                                other_files=[logger_file], logger=logger,
                                region_name=region_name,
                                file_name_prefix=file_name_prefix
                            )

                except RateLimitExceededException:
                    logger.info(msg='Github API rate limit reached')
                    self._git = get_git_instance(
                        number_of_attempts=10, logger=logger
                    )
                    repo_data = RepositoryData(git=self._git)
                    continue
                except UnknownObjectException:
                    not_suitable_ids.add(repo_id)
                    logger.info(
                        msg=f'Added not suitable repo ID: {repo_id}'
                    )
                    continue
                except GithubException:
                    logger.info(msg='Encoutered an incomplete repository')
                    continue
                except ReadTimeout:
                    logger.info(msg='Newtwork issue')
                    sleep(10)
                    continue
                except NoAPICalls:
                    logger.info(msg='API calls were not granted')
                    return

        finally:
            self.save_and_upload_all(
                file_set_tuples=file_set_tuples,
                other_files=[logger_file], logger=logger,
                region_name=region_name,
                file_name_prefix=file_name_prefix
            )
            logger.info(msg='End of the search')

    def compute_features(
            self, logger_name: str, features_file: str, ids_file_name: str,
            csv_file_name: str, region_name: str, file_name_prefix: str,
            partial_upload_size: int = 10
    ) -> None:
        try:
            logger = setup_logger(
                name=__name__, file=logger_name,
                format=logger_config_values['format'],
                level=logger_config_values['level']
            )
            self.download_all(
                file_names=[ids_file_name, csv_file_name],
                region_name=region_name, file_name_prefix=file_name_prefix,
                logger=logger
            )

            processed_names = self.load_visited_ids(
                dat_file='main_names.dat', logger=logger
            )

            repo_data = RepositoryData(git=self._git)
            features = self.load_features(features_file=features_file)
            repo_computed_counter = 0
            computed_ids = set()

            if not Path(csv_file_name).is_file():
                self.prepare_csv(features=features, file_name=csv_file_name)

            repo_ids = self.load_visited_ids(
                dat_file=ids_file_name, logger=logger
            )
            logger.debug(msg=f'IDs set size: {len(repo_ids)}')

            ids_all = len(repo_ids)
            ids_count = 0

            logger_file = logger_file_name(logger=logger)
            logger.info(msg='Start of computation')
            for repo_id in repo_ids:
                try:
                    logger.info(msg=f'Computing repo: {repo_id}')
                    repo_data.set_repo(repo_name_or_id=repo_id)

                    if repo_data.repo_name() in processed_names:
                        logger.info(msg='Duplicate repo')
                        continue

                    self.write_to_csv(
                        data=repo_data.get_row(
                            features=features, logger=logger
                        ),
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
                            file_name_prefix=file_name_prefix,
                            logger=logger
                        )
                except RateLimitExceededException:
                    logger.info(msg='Github API rate limit reached')
                    self._git = get_git_instance(
                        number_of_attempts=10, logger=logger
                    )
                    repo_data = RepositoryData(git=self._git)
                    continue
                except UnknownObjectException:
                    logger.info(msg='Encountered a removed repository')
                    continue
                except GithubException:
                    logger.info(msg='Encoutered an incomplete repository')
                    continue
                except (ReadTimeout, ConnectionError):
                    logger.info(msg='Newtwork issue')
                    sleep(10)
                    continue
                except NoAPICalls:
                    logger.info(msg='API calls were not granted')
                    return

        finally:
            remaining_ids = repo_ids - computed_ids
            self.save_and_upload_all(
                file_set_tuples=[(ids_file_name, remaining_ids)],
                other_files=[csv_file_name, logger_file], logger=logger,
                region_name=region_name,
                file_name_prefix=file_name_prefix
            )
            logger.info(msg='End of the search')
