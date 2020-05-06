
import csv
from typing import Any, List, Optional

from .repository_data import RepositoryData

import pandas as pd


class Dataset:

    def __init__(
            self, links_file_name: str, headers: List[str]
    ) -> None:
        self.links_file_name: str = links_file_name
        # self.headers = headers
        # self.data_raw: Optional[List[List[Any]]] = None
        # self.data_df: Optional[pd.DataFrame] = None

    # def compile_data(
    #         self, size_limit: int = 10, age_limit: int = 10,
    #         contributors_limit: int = 5, pull_last_age_limit: int = 5
    # ) -> None:
    #     with open(self.links_file_name, 'r') as file:
    #         for link in file.readlines():
    #             rd = RepositoryData(url=link)
    #             if (
    #                     rd.size > size_limit and
    #                     rd.age > age_limit and
    #                     rd.contributors_count > contributors_limit and
    #                     rd.pull_last_age > pull_last_age_limit
    #             ):
    #                 dataset_line = []
    #                 # TODO append all the relevant data to the dataset_line
    #
    #                 self.data_raw.append(dataset_line)

    def create_df(self) -> None:
        if self.data_raw is None:
            raise ValueError('Dataset is empty')
        self.data_df = pd.DataFrame(self.data_raw, columns=self.headers)

    def export_csv(self, file_name: str = None) -> None:
        with open(file_name or 'dataset.csv', 'w') as file:
            writer = csv.writer(file, delimeter=',')
            writer.writerow(self.headers)
            writer.writerows(self.data_raw)
