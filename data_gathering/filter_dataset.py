
from typing import List

from github.GithubException import RateLimitExceededException
from pandas import Dataframe, read_csv, Series

from data_gathering import GIT_INSTANCE
from .repository_data import RepositoryData
from waiting import wait_for_api_calls


class CouldNotRecomputeRepo(Exception):
    pass


def save_to_csv(dataset: Dataframe, file_name: str) -> None:
    dataset.to_csv(file_name, index=False, header=True)


def find_incomplete_rows(dataset: Dataframe) -> Series:
    return dataset[dataset.isna().any(axis=1)]['repo_name']


def substitude_row(
    dataset: Dataframe, repo_name: str, new_row: List[str]
) -> None:
    dataset.drop(
        labels=dataset[dataset['repo_name'] == repo_name].index, inplace=True
    )
    dataset = dataset.append(other=new_row)


def recompute_and_substitude_rows(file_name: str, features: List[str]) -> None:
    dataset = read_csv(filepath_or_buffer=file_name)
    incomplete_rows = find_incomplete_rows(dataset=dataset)
    rd = RepositoryData(git=GIT_INSTANCE)
    rate_limit_exceeded = False

    for repo in incomplete_rows:
        try:
            complete_repo = rd.get_row(features=features)
            rate_limit_exceeded = False
            substitude_row(
                dataset=dataset, repo_name=repo, new_row=complete_repo
            )
        except RateLimitExceededException:
            if not rate_limit_exceeded:
                rate_limit_exceeded = True
            else:
                raise CouldNotRecomputeRepo
            wait_for_api_calls(git=GIT_INSTANCE)
            continue
