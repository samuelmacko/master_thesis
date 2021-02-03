
from argparse import ArgumentParser, RawTextHelpFormatter

from data_gathering.config import config_values
from data_gathering.dataset import Dataset


parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
parser.add_argument(
    '-s', '--search-repos', action='store_true', dest='search', default=False,
    help='Search through Github repositories, evaluate them and save ' +
         'their IDs into corresponding .dat files \n' +
         'parameters expected in configs/data_gathering/gathering.yml: \n' +
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
    '-c', '--compute-features', dest='compute',
    help='Compute features for repositories and store results in \n' +
         'corresponding .csv files' +
         'parameters expected in configs/data_gathering/gathering.yml: \n' +
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

dataset = Dataset()

s3_config_values = config_values['s3_handling']
if args.search:
    search_config_values = config_values['search_repos']
    dataset.search_repos(
        end_condition=search_config_values['end_condition'],
        value=search_config_values['end_value'],
        from_year=search_config_values['from_year'],
        to_year=search_config_values['to_year'],
        partial_upload_size=search_config_values['partial_upload_size'],
        unmaintained_ids_file=search_config_values['unmaintained_ids'],
        maintained_ids_file=search_config_values['maintained_ids'],
        not_suitable_ids_file=search_config_values['not_suitable_ids'],
        file_name_prefix=s3_config_values['file_name_prefix'],
        region_name=s3_config_values['region']
    )

elif args.compute:
    compute_config_values = config_values['compute_features']
    if args.compute == 'unmaintained':
        csv_file = compute_config_values['unmaintained']['csv_file']
        ids_file = compute_config_values['unmaintained']['ids_file']
    elif args.compute == 'maintained':
        csv_file = compute_config_values['maintained']['csv_file']
        ids_file = compute_config_values['maintained']['ids_file']
    else:
        print('Wrong --compute_features value')
        exit(1)

    dataset.compute_features(
        features_file=compute_config_values['features'],
        partial_upload_size=compute_config_values['partial_upload_size'],
        csv_file_name=csv_file,
        ids_file_name=ids_file,
        file_name_prefix=s3_config_values['file_name_prefix'],
        region_name=s3_config_values['region']
    )
