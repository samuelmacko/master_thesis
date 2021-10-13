
from github import Github

from os import getenv

from .config import config_values


_GITHUB_ACCESS_TOKEN = getenv('GITHUB_ACCESS_TOKEN')
GIT_INSTANCE = Github(login_or_token=_GITHUB_ACCESS_TOKEN)

_GITHUB_ACCESS_TOKEN_PETIN = getenv('GITHUB_ACCESS_TOKEN_PETIN')
GIT_INSTANCE_PETIN = Github(login_or_token=_GITHUB_ACCESS_TOKEN_PETIN)

logger_config_values = config_values['logger']
