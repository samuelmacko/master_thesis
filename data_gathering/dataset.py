
import csv
from datetime import date, datetime
import logging
from marshal import dump, load
from os import getenv
from pathlib import Path
from random import randrange
from time import sleep
from typing import Any, List, Optional, Set
from yaml import safe_load

from github import Github
from github.GithubException import (
    RateLimitExceededException, UnknownObjectException
)

from .enums import EndCondition
from .repository_data import RepositoryData
from .s3_handler import S3Handler


_GITHUB_ACCESS_TOKEN = getenv('GITHUB_ACCESS_TOKEN')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('data_gathering.log')
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(fmt=formatter)
console_handler.setFormatter(fmt=formatter)

logger.addHandler(hdlr=file_handler)
logger.addHandler(hdlr=console_handler)


class Dataset:

    def __init__(self) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)

    @staticmethod
    def load_features(features_file: str) -> List[str]:
        with open(features_file, 'r') as f:
            return safe_load(f)

    @staticmethod
    def prepare_csv(features: List[str], file_name: str) -> None:
        with open(file_name, 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(features)

    @staticmethod
    def write_to_csv(data: List[Any], file_name: str) -> None:
        with open(file_name, 'a') as f:
            writer = csv.writer(f, delimiter=',')
            data = [str(col) for col in data]
            writer.writerow(data)

    @staticmethod
    def save_visited_ids(dat_file: str, visited_ids: Set[int]) -> None:
        with open(dat_file, 'wb') as f:
            dump(visited_ids, f)

    @staticmethod
    def load_visited_ids(dat_file: str) -> Optional[Set[int]]:
        try:
            with open(dat_file, 'rb') as f:
                try:
                    return load(f)
                except EOFError:
                    return set()
        except FileNotFoundError:
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

    def save_all(
            self, unmaintained_ids_file: str, unmaintained_ids_set: Set,
            maintained_ids_file: str, maintained_ids_set: Set,
            not_suitable_ids_file: str, not_suitable_ids_set: Set
    ) -> None:
        self.save_visited_ids(
            dat_file=unmaintained_ids_file,
            visited_ids=unmaintained_ids_set
        )
        self.save_visited_ids(
            dat_file=maintained_ids_file, visited_ids=maintained_ids_set
        )
        self.save_visited_ids(
            dat_file=not_suitable_ids_file,
            visited_ids=not_suitable_ids_set
        )
        logger.info(msg='IDs saved to files')

    def upload_all(
        self, unmaintained_ids_file: str, maintained_ids_file: str,
        not_suitable_ids_file: str, region_name: str = None
    ) -> None:
        s3_handler = S3Handler(region_name=region_name)
        if not s3_handler.bucket_exits_check():
            s3_handler.create_bucket()

        s3_handler.upload_file(file_name=unmaintained_ids_file)
        s3_handler.delete_oldest_object_with_prefix(
            prefix=unmaintained_ids_file
        )
        s3_handler.upload_file(file_name=maintained_ids_file)
        s3_handler.delete_oldest_object_with_prefix(prefix=maintained_ids_file)
        s3_handler.upload_file(file_name=not_suitable_ids_file)
        s3_handler.delete_oldest_object_with_prefix(
            prefix=not_suitable_ids_file
        )
        logger.info(msg='IDs files uploaded to the S3 bucket')

    def search_repos(
            self, from_year: str, to_year: str,
            unmaintained_ids_file: str, maintained_ids_file: str,
            not_suitable_ids_file: str,
            end_condition: EndCondition, value: int,
            region_name: str
    ) -> None:
        repo_data = RepositoryData(git=self._git)
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
                except RateLimitExceededException:
                    logger.info(
                        msg='Github API rate limit reached, ' +
                            'waiting for an hour'
                    )
                    sleep(3600)
                    continue
                except UnknownObjectException:
                    not_suitable_ids.add(generated_id)
                    logger.info(
                        msg=f'Added not suitable repo ID: {generated_id}'
                    )
                    continue

        finally:
            self.save_all(
                unmaintained_ids_file=unmaintained_ids_file,
                unmaintained_ids_set=unmaintained_ids,
                maintained_ids_file=maintained_ids_file,
                maintained_ids_set=maintained_ids,
                not_suitable_ids_file=not_suitable_ids_file,
                not_suitable_ids_set=not_suitable_ids
            )
            self.upload_all(
                unmaintained_ids_file=unmaintained_ids_file,
                maintained_ids_file=maintained_ids_file,
                not_suitable_ids_file=not_suitable_ids_file,
                region_name=region_name
            )
            logger.info(msg='End of the search')

    def compute_features(
            self, features_file: str, unmaintained_ids_file: str,
            maintained_ids_file: str, maintained_csv_file: str,
            unmaintained_csv_file: str
    ) -> None:
        repo_data = RepositoryData(git=self._git)

        features = self.load_features(features_file=features_file)

        for file in (maintained_ids_file, unmaintained_ids_file):

            if file == maintained_ids_file:
                csv_file = maintained_csv_file
            else:
                csv_file = unmaintained_csv_file

            if not Path(csv_file).is_file():
                self.prepare_csv(features=features, file_name=csv_file)

            repo_ids = self.load_visited_ids(dat_file=file)
            ids_all = len(repo_ids)
            ids_count = 0

            for repo_id in repo_ids:
                repo_data.set_repo(repo_id=repo_id)
                self.write_to_csv(
                    data=repo_data.get_row(features=features),
                    file_name=csv_file
                )
                logger.info(
                    msg=f'Added row with ID: {repo_id} to: {csv_file}, ' +
                        f'rank: {ids_count} / {ids_all}'
                )
                repo_ids.remove(repo_id)
