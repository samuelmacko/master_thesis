
from data_gathering.dataset import Dataset
from data_gathering.repository_data import RepositoryData

# dataset = Dataset(links_file_name='filler')

repo = RepositoryData(url='kedacore/keda-olm-operator')
print(repo.pulls_open())

pass