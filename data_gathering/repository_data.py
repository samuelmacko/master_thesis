
from datetime import datetime
import os
from typing import List

from dateutil.relativedelta import relativedelta
from github import Github
from github.GithubException import UnknownObjectException
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
        return self._repo.get_commits(since=threshold_date).totalCount

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
            date = self._repo.created_at
        else:
            date = datetime.now().date() - relativedelta(weeks=weeks)
        return datetime.combine(date, datetime.min.time())

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

    def max_days_without_commit(self, weeks: int = 104) -> int:
        threshold_date = self.threshold_date(weeks=weeks)
        commits = self._repo.get_commits(since=threshold_date)
        max_days = 0
        prev_commit = commits[0]
        for commit in commits[1:]:
            days = (
                    prev_commit.commit.author.date - commit.commit.author.date
            ).days
            if days > max_days:
                max_days = days

        return max_days

    def owner_account_age(self) -> int:
        return self.datetime_to_days(dtime=self._repo.owner.created_at)

    @staticmethod
    def datetime_to_days(dtime: datetime) -> int:
        return (datetime.now() - dtime).days

    def avg_dev_account_age(self) -> float:
        contributors = self._repo.get_contributors()
        collective_age = 0
        for contributor in contributors:
            collective_age += self.datetime_to_days(
                dtime=contributor.created_at
            )

        return collective_age / contributors.totalCount

    def documentation_changes_frequency(self, weeks: int = 104) -> float:
        threshold_date = self.threshold_date(weeks=weeks)
        commits = list(self._repo.get_commits(since=threshold_date))
        counter = 0
        for commit in commits:
            file_names = [file.filename for file in commit.files]
            for file_name in file_names:
                if 'README' in file_name:
                    counter += 1

        return counter / len(commits)

    def documentation_changes_additions(self, weeks: int = 104) -> float:
        threshold_date = self.threshold_date(weeks=weeks)
        commits = list(self._repo.get_commits(since=threshold_date))
        counter = 0
        additions = 0
        for commit in commits:
            files = [file for file in commit.files]
            for file in files:
                if 'README' in file.filename:
                    counter += 1
                    additions += file.additions - file.deletions

        return additions / counter

    def _get_dirs(self) -> List[str]:
        dirs = [
            dir.path for dir in self._repo.get_contents(path='')
            if dir.type == 'dir'
        ]
        if len(dirs) == 0:
            return dirs

        i = 0
        while i < len(dirs):
            subdirs = [
                dir.path for dir in self._repo.get_contents(path=dirs[i])
                if dir.type == 'dir'
            ]
            dirs += subdirs
            i += 1
        return dirs

    def _has_file(self, file_names: List[str]) -> bool:
        files = [os.path.basename(file) for file in self._get_dirs()]
        for file in file_names:
            if file.lower() in files:
                return True
        return False

    def has_test(self) -> bool:
        return self._has_file(file_names=['test', 'tests', 't', 'spec'])

    def has_doc(self) -> bool:
        return self._has_file(
            file_names=['doc', 'docs', 'document', 'documents']
        )

    def has_example(self) -> bool:
        return self._has_file(file_names=['example', 'examples'])

    def has_readme(self) -> bool:
        try:
            self._repo.get_readme()
            return True
        except UnknownObjectException:
            return False

    def owners_projects_count(self) -> int:
        repos = self._repo.owner.public_repos
        return repos if repos else 0

    def owner_following(self) -> int:
        return self._repo.owner.following

    def owner_followers(self) -> int:
        return self._repo.owner.followers

    def devs_followers_avg_count(self) -> float:
        contributors = self._repo.get_contributors()
        count = 0
        for contributor in contributors:
            count += contributor.followers
        return count / contributors.totalCount

    def devs_following_avg_count(self) -> float:
        contributors = self._repo.get_contributors()
        count = 0
        for contributor in contributors:
            count += contributor.following
        return count / contributors.totalCount

    def commits_by_dev_with_most_commits(self) -> int:
        return 0
