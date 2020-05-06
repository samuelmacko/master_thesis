
from datetime import datetime
import os

from dateutil.relativedelta import relativedelta
from github import Github
from github.Repository import Repository

from .enums import AccountType


_GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')


class RepositoryData:

    def __init__(self, url: str) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)
        self._repo: Repository = self._git.get_repo(full_name_or_id=url)

    def pulls_count(self, state: str = 'open', weeks: int = 104) -> int:
        if state == 'open' or state == 'closed':
            pulls = self._repo.get_pulls(state=state)
        elif state == 'merged':
            pulls = [
                pull for pull in self._repo.get_pulls(state='all')
                if pull.merged
            ]
        else:
            raise ValueError('Wrong value for state')

        counter = 0
        threshold_date = self.threshold_date(weeks=weeks)
        for pull in pulls:
            if pull.created_at < threshold_date:
                counter += 1
        return counter

    def issues_count(self, state: str = 'open', weeks: int = 104) -> int:
        if state == 'open' or state == 'closed':
            issues = self._repo.get_issues(state=state)
        else:
            raise ValueError('Wrong value for state')

        counter = 0
        threshold_date = self.threshold_date(weeks=weeks)
        for issue in issues:
            if issue.created_at < threshold_date:
                counter += 1
        return counter

    def commits_count(self, weeks: int = 104) -> int:
        threshold_date = self.threshold_date(weeks=weeks)
        return len(self._repo.get_commits(since=threshold_date))

    def branches_count(self) -> int:
        return len(self._repo.get_branches())

    def releases_count(self, weeks: int = 104) -> int:
        releases = self._repo.get_releases()
        counter = 0
        threshold_date = self.threshold_date(weeks=weeks)
        for release in releases:
            if release.created_at < threshold_date:
                counter += 1
        return counter

    def threshold_date(self, weeks: int = 104) -> datetime:
        if weeks == 0:
            return self._repo.created_at

        present_date = datetime.now().date()
        return present_date - relativedelta(weeks=weeks)

    def owner_type(self) -> AccountType:
        owner_type = self._repo.owner.type
        if owner_type == 'Organization':
            return AccountType.Organization
        elif owner_type == 'User':
            return AccountType.User
        else:
            raise ValueError('Unsupported account type')

    def watchers_count(self) -> int:
        return self._repo.watchers_count

    def forks_count(self) -> int:
        return self._repo.forks_count

    def stargazers_count(self) -> int:
        return self._repo.stargazers_count

    def age(self) -> int:
        present_date = datetime.now().date()
        created_date = self._repo.created_at
        return (present_date - created_date).days
