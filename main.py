
from argparse import ArgumentParser, RawTextHelpFormatter
from yaml import safe_load

from data_gathering.dataset import Dataset


parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
parser.add_argument(
    '-s', '--search-repos', action='store_true', dest='search', default=False,
    help='Search through Github repositories, evaluate them and save ' +
         'their IDs into corresponding .dat files \n' +
         'parameters expected in configs/gathering.yml: \n' +
         '  - from_year         - repositories created before this year' +
         'will not be considered \n' +
         '  - to_year           - repositories created after this year' +
         'will not be considered \n' +
         '  - unmaintained_ids  - path to .dat file containing IDs of' +
         'unmaintained repositories \n' +
         '  - maintained_ids    - path to .dat file containing IDs of' +
         'maintained repositories \n' +
         '  - not_suitable_ids  - path to .dat file containing IDs of' +
         'not suitable repositories \n' +
         '  - end_condition     - end condition \n' +
         '  - end_value         - value of the end condition'
)
parser.add_argument(
    '-c', '--compute-features', action='store_true', dest='compute',
    default=False,
    help='Compute features for repositories and store results in \n' +
         'corresponding .csv files' +
         'parameters expected in configs/gathering.yml: \n' +
         '  - features_file         - path to file containing a list of' +
         'features \n' +
         '  - unmaintained_ids      - path to .dat file containing IDs of' +
         'unmaintained repositories \n' +
         '  - maintained_ids        - path to .dat file containing IDs of' +
         'maintained repositories \n' +
         '  - maintained_csv_file   - path to file into which will be' +
         'saved features of maintained repositories \n' +
         '  - unmaintained_csv_file - path to file into which will be' +
         'saved features of maintained repositories'
)

args = parser.parse_args()

if args.search and args.compute:
    print('Use at most one argument')
    exit(1)

with open('configs/gathering.yml', 'r') as f:
    gathering_config = safe_load(f)

dataset = Dataset()

if args.search:
    dataset.search_repos(
        from_year=gathering_config['from_year'],
        to_year=gathering_config['to_year'],
        unmaintained_ids_file=gathering_config['unmaintained_ids'],
        maintained_ids_file=gathering_config['maintained_ids'],
        not_suitable_ids_file=gathering_config['not_suitable_ids'],
        end_condition=gathering_config['end_condition'],
        value=gathering_config['end_value'],
        region_name=gathering_config['s3_region'],
        bucket_name=gathering_config['s3_bucket_name']
    )

if args.compute:
    dataset.compute_features(
        features_file=gathering_config['features_file'],
        maintained_ids_file=gathering_config['maintained_ids'],
        unmaintained_ids_file=gathering_config['unmaintained_ids'],
        maintained_csv_file=gathering_config['maintained_csv_file'],
        unmaintained_csv_file=gathering_config['unmaintained_csv_file']
    )
