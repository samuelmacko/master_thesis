
from data_gathering.dataset import Dataset
from data_gathering.repository_data import RepositoryData

# dataset = Dataset(links_file_name='filler')

repo = RepositoryData(url='kedacore/keda-olm-operator')
# repo = RepositoryData(url='samuelmacko/keda-scripts')
# print(repo.max_days_without_commit(weeks=2))
# print(repo.commits_count())
print(repo.devs_following_avg_count())

pass