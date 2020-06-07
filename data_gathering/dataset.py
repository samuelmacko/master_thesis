
import csv
from os import getenv
from pathlib import Path
from typing import Any, List
from yaml import safe_load

from github import Github

from .repository_data import RepositoryData


_GITHUB_ACCESS_TOKEN = getenv('GITHUB_ACCESS_TOKEN')


class Dataset:

    def __init__(
            self, links_file_name: str, features_file: str,
            last_visited_node: int = 0
    ) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)
        self.links_file_name: str = links_file_name
        self.features: List[Any] = self.load_features(
            features_file=features_file
        )
        self.last_visited_node = last_visited_node

    @staticmethod
    def load_features(features_file: str) -> List[str]:
        with open(features_file, 'r') as f:
            return safe_load(f)

    def write_to_csv(self, data: List[str]) -> None:
        if not Path(self.links_file_name).is_file():
            with open(self.links_file_name, 'w') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(self.features)
        with open(self.links_file_name, 'a') as f:
            writer = csv.writer(f, delimiter=',')
            data = [str(col) for col in data]
            writer.writerow(data)

    def search_repos(self) -> None:
        repos = self._git.get_repos(since=self.last_visited_node)
        repo_data = RepositoryData(git=self._git)
        for repo in repos:
            repo_data.repo = repo.full_name
            if repo_data.suitable():
                self.write_to_csv(repo_data.get_row(features=self.features))
