
from yaml import safe_load

with open('configs/data_gathering/gathering.yml', 'r') as f:
    config_values = safe_load(f)
