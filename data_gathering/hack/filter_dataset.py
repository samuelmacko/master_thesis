
from csv import DictReader, reader, writer
from typing import Dict, List


def load_from_csv(
    file_name: str, as_dict: bool = False
) -> List[Dict[str, str]]:
    dataset = []
    with open(file=file_name, mode='r') as raw_dataset:
        if as_dict:
            csv_reader = DictReader(f=raw_dataset)
        else:
            csv_reader = reader(raw_dataset)

        for line in csv_reader:
            dataset.append(line)
    return dataset


def save_to_csv(data: List[str], file_name: str) -> None:
    with open(file=file_name, mode='w') as f:
        csv_writer = writer(f, delimiter=',')
        for line in data:
            csv_writer.writerow(line)


def find_incomplete_rows(dataset: List[Dict[str, str]]) -> List[str]:
    incomplete_rows_repos = []
    for line in dataset:
        if 'Could not compute' in line.values():
            incomplete_rows_repos.append(line['repo_name'])
    return incomplete_rows_repos


def substitude_row(
    dataset: List[str], repo_name: str, new_row: List[str]
) -> None:
    for line in dataset:
        if line[0] == repo_name:
            dataset.remove(line)
    dataset.append(new_row)
    return dataset
