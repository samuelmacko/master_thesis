
from yaml import safe_load

from data_gathering.dataset import Dataset
from data_gathering.repository_data import RepositoryData

with open('configs/gathering.yml', 'r') as f:
    gatherint_config = safe_load(f)

dataset = Dataset(
    links_file_name=gatherint_config['csv_file_name'],
    last_visited_node=gatherint_config['last_visited_node'],
    features_file='configs/features.yml'
)

# repo = RepositoryData(url='kedacore/keda-olm-operator')
# repo = RepositoryData(url='kedacore/keda')
repo = RepositoryData(url='samuelmacko/keda-scripts')
# repo = RepositoryData(url='chef-boneyard/chef-repo')
# repo = RepositoryData(url='bhrugen/BookListRazor')
# repo = RepositoryData(url='oVirt/ovirt-web-ui')

ff = dataset.load_features('configs/features.yml')
dataset.write_to_csv(data=repo.get_row(features=ff))
