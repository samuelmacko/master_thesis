
from github import Github

from os import getenv

from .config import config_values


_GITHUB_ACCESS_TOKEN_0 = getenv('GITHUB_ACCESS_TOKEN_0')
_GITHUB_ACCESS_TOKEN_1 = getenv('GITHUB_ACCESS_TOKEN_1')
_GITHUB_ACCESS_TOKEN_2 = getenv('GITHUB_ACCESS_TOKEN_2')

GIT_INSTANCE_0 = Github(login_or_token=_GITHUB_ACCESS_TOKEN_0)
GIT_INSTANCE_1 = Github(login_or_token=_GITHUB_ACCESS_TOKEN_1)
GIT_INSTANCE_2 = Github(login_or_token=_GITHUB_ACCESS_TOKEN_2)

GITHUB_INSTANCES = [GIT_INSTANCE_0, GIT_INSTANCE_1, GIT_INSTANCE_2]

logger_config_values = config_values['logger']

