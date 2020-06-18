
import csv
from datetime import date, datetime
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


_GITHUB_ACCESS_TOKEN = getenv('GITHUB_ACCESS_TOKEN')


class Dataset:

    def __init__(self, features_file: str) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)
        self.features: List[Any] = self.load_features(
            features_file=features_file
        )

    @staticmethod
    def load_features(features_file: str) -> List[str]:
        with open(features_file, 'r') as f:
            return safe_load(f)

    def write_to_csv(self, data: List[str], file_name: str) -> None:
        if not Path(file_name).is_file():
            with open(file_name, 'w') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(self.features)
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
        with open(dat_file, 'rb') as f:
            try:
                return load(f)
            except EOFError:
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

    def search_repos(
            self, from_year: str, to_year: str,
            unmaintained_ids_file: str, maintained_ids_file: str,
            not_suitable_ids_file: str,
            end_condition: EndCondition, value: int
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

        while len(eval(end_condition.value)) < value:
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
                    else:
                        maintained_ids.add(generated_id)
                else:
                    not_suitable_ids.add(generated_id)
            except RateLimitExceededException:
                sleep(3600)
                continue
            except UnknownObjectException:
                not_suitable_ids.add(generated_id)
                continue
            finally:
                self.save_visited_ids(
                    dat_file=unmaintained_ids_file,
                    visited_ids=unmaintained_ids
                )
                self.save_visited_ids(
                    dat_file=maintained_ids_file, visited_ids=maintained_ids
                )
                self.save_visited_ids(
                    dat_file=not_suitable_ids_file,
                    visited_ids=not_suitable_ids
                )
