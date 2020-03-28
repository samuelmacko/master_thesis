
import csv
from typing import List, Any

from .repository_data import RepositoryData

import pandas as pd


class Dataset:

    def __init__(self, links_file_name: str) -> None:
        self.links_file_name: str = links_file_name
        self.data: List[List[Any]] = []
        # RepositoryData(url=)
        rd = RepositoryData(url='oVirt/ovirt-web-ui')
        # print(rd.releases_avg_download_count())
        print(rd.code_length)

    # def compile_data(self) -> None:
    #     with open(self.links_file_name, 'r') as file:
    #         for link in file.readlines():
    #             rd = RepositoryData(url=link, git=self.git)
    #             self.data.append(rd.export_line())
    #
    # def get_df(self) -> pd.DataFrame:
    #     return pd.DataFrame(self.data, columns=self.headers)
    #
    # def export_csv(self, file_name: str = None) -> None:
    #     with open(file_name or 'dataset.csv', 'w') as file:
    #         writer = csv.writer(file, delimeter=',')
    #         writer.writerow(self.headers)
    #         writer.writerows(self.data)
