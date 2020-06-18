
from yaml import safe_load

from data_gathering.dataset import Dataset
from data_gathering.enums import EndCondition

with open('configs/gathering.yml', 'r') as f:
    gatherint_config = safe_load(f)

dataset = Dataset(features_file='configs/features.yml')
dataset.search_repos(
    from_year='2013', to_year='2018',
    unmaintained_ids_file=gatherint_config['unmaintained_ids'],
    maintained_ids_file=gatherint_config['maintained_ids'],
    not_suitable_ids_file=gatherint_config['not_suitable_ids'],
    end_condition=EndCondition.Unmaintained, value=5
)
