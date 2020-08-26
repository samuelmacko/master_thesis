
from datetime import datetime, timedelta
from math import ceil
from os import path
from re import compile
from typing import Any, List, Optional, Set, Union
from yaml import safe_load

from dateutil.relativedelta import relativedelta
from github import Github
from github.GithubException import (
    RateLimitExceededException, UnknownObjectException
)
from github.NamedUser import NamedUser
from github.Repository import Repository

from .config import config_values
from .enums import AccountType
from logger import setup_logger
from .waiting import wait_for_api_calls


COMMIT_LAST_MODIFIED_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

logger_config_values = config_values['logger']
logger = setup_logger(
    name=__name__, file=logger_config_values['file'],
    format=logger_config_values['format'], level=logger_config_values['level']
)


class RepositoryData:

    def __init__(self, git: Github) -> None:
        self._git: Github = git
        self._repo: Optional[Repository] = None

    def set_repo(
        self, repo_name_or_id: str = None, repo: Repository = None
    ) -> None:
        if repo_name_or_id:
            self._repo = self._git.get_repo(full_name_or_id=repo_name_or_id)
        if repo:
            self._repo = repo

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
        threshold_date = self.threshold_datetime(weeks=weeks)
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
        threshold_date = self.threshold_datetime(weeks=weeks)
        for issue in issues:
            if issue.created_at < threshold_date:
                counter += 1
        return counter

    def commits_count(self, weeks: int = 104) -> int:
        threshold_date = self.threshold_datetime(weeks=weeks)
        return self._repo.get_commits(since=threshold_date).totalCount

    def branches_count(self) -> int:
        return self._repo.get_branches().totalCount

    def releases_count(self, weeks: int = 104) -> int:
        releases = self._repo.get_releases()
        counter = 0
        threshold_date = self.threshold_datetime(weeks=weeks)
        for release in releases:
            if release.created_at < threshold_date:
                counter += 1
        return counter

    def last_commit_datetime(self) -> datetime:
        return datetime.strptime(
            self._repo.get_commits()[0].last_modified,
            COMMIT_LAST_MODIFIED_FORMAT
        )

    def last_commit_age(self) -> int:
        return (
            datetime.now().date() - self.last_commit_datetime().date()
        ).days

    def first_commit_datetime(self) -> datetime:
        return datetime.strptime(
            self._repo.get_commits().reversed[0].last_modified,
            COMMIT_LAST_MODIFIED_FORMAT
        )

    def threshold_datetime(self, weeks: int = 104) -> datetime:
        if weeks == 0:
            date = self._repo.created_at
        else:
            date = self.last_commit_datetime() - relativedelta(weeks=weeks)
        return datetime.combine(date, datetime.min.time())

    def threshold_date(self, weeks: int = 104) -> datetime:
        if weeks == 0:
            date = self._repo.created_at
        else:
            date = datetime.now().date() - relativedelta(weeks=weeks)
        return date

    def owner_type(self) -> AccountType:
        owner_type = self._repo.owner.type
        if owner_type == 'Organization':
            return AccountType.Organization.value
        elif owner_type == 'User':
            return AccountType.User.value
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
        created_date = self._repo.created_at.date()
        return (present_date - created_date).days

    def max_days_without_commit(self, weeks: int = 104) -> int:
        threshold_date = self.threshold_datetime(weeks=weeks)
        commits = list(self._repo.get_commits(since=threshold_date))
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

        contributors_count = contributors.totalCount
        # not really sure why or how this happens, but sometimes, it happens
        if contributors_count == 0:
            return 0
        else:
            return collective_age / contributors_count

    def documentation_changes_frequency(self, weeks: int = 104) -> float:
        threshold_date = self.threshold_datetime(weeks=weeks)
        commits = list(self._repo.get_commits(since=threshold_date))
        counter = 0
        for commit in commits:
            file_names = [file.filename for file in commit.files]
            for file_name in file_names:
                if 'README' in file_name:
                    counter += 1

        return counter / len(commits)

    def documentation_changes_additions(self, weeks: int = 104) -> float:
        threshold_date = self.threshold_datetime(weeks=weeks)
        commits = list(self._repo.get_commits(since=threshold_date))
        counter = 0
        additions = 0
        for commit in commits:
            files = [file for file in commit.files]
            for file in files:
                if 'README' in file.filename:
                    counter += 1
                    additions += file.additions - file.deletions

        if counter == 0:
            return 0
        return additions / counter

    @staticmethod
    def _filter_dirs(dirs: List[str]) -> List[str]:
        with open('configs/vendor.yml', 'r') as vendor_file:
            vendor_regexes = safe_load(vendor_file)
        regexes = [compile(regex) for regex in vendor_regexes]
        for dir in dirs:
            if any([rgx.match(dir) for rgx in regexes]):
                dirs.remove(dir)
        return dirs

    def _get_dirs(self) -> List[str]:
        dirs = self._filter_dirs(dirs=[
            dir.path for dir in self._repo.get_contents(path='')
            if dir.type == 'dir'
        ])
        if len(dirs) == 0:
            return dirs

        i = 0
        while i < len(dirs):
            subdirs = self._filter_dirs(dirs=[
                dir.path for dir in self._repo.get_contents(path=dirs[i])
                if dir.type == 'dir'
            ])
            dirs += subdirs
            i += 1
        return dirs

    def _get_files(self) -> List[str]:
        files = []
        for dir in self._get_dirs():
            files.extend([
                file.path for file in self._repo.get_contents(path=dir)
                if file.type == 'file'
            ])
        return files

    def _has_file(self, file_names: List[str]) -> bool:
        files = [path.basename(file) for file in self._get_dirs()]
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

    def owner_projects_count(self) -> int:
        repos = self._repo.owner.public_repos
        return repos if repos else 0

    def owner_following(self) -> int:
        return self._repo.owner.following

    def owner_followers(self) -> int:
        return self._repo.owner.followers

    def devs_followers_avg(self) -> float:
        contributors = self._repo.get_contributors()
        count = 0
        for contributor in contributors:
            count += contributor.followers
        contributors_count = contributors.totalCount
        if contributors_count == 0:
            return 0
        else:
            return count / contributors_count

    def devs_following_avg(self) -> float:
        contributors = self._repo.get_contributors()
        count = 0
        for contributor in contributors:
            count += contributor.following
        contributors_count = contributors.totalCount
        if contributors_count == 0:
            return 0
        else:
            return count / contributors_count

    def commits_by_dev_with_most_commits(self) -> int:
        commits = self._repo.get_commits()
        contr_dict = {}
        for commit in commits:
            name = commit.commit.author.name
            if name in contr_dict:
                contr_dict[name] += 1
            else:
                contr_dict[name] = 1

        max_contriburor = max(contr_dict, key=contr_dict.get)
        return contr_dict[max_contriburor]

    def _contributors_divided(
        self, threshold: int = 104
    ) -> Union[Set[str], Set[str]]:
        threshold_date = self.threshold_datetime(weeks=threshold)
        commits_before = self._repo.get_commits(until=threshold_date)
        commits_after = self._repo.get_commits(since=threshold_date)
        contributors_old = set()
        contributors_new = set()
        for commit in commits_before:
            name = commit.commit.author.name
            if name not in contributors_old:
                contributors_old.add(name)

        for commit in commits_after:
            name = commit.commit.author.name
            if name not in contributors_old:
                contributors_new.add(name)

        return contributors_new, contributors_old

    def magneticness(self, threshold: int = 104) -> float:
        new, old = self._contributors_divided(threshold=threshold)
        if len(old) == 0:
            return 0
        return len(new) / len(old)

    @staticmethod
    def _days_to_datetime(days: int):
        date = datetime.now().date() - timedelta(days=days)
        return datetime.combine(date, datetime.min.time())

    def stickiness(
            self, new_threshold: int = 104, sticky_threshold: int = 52
    ) -> float:
        new, _ = self._contributors_divided(threshold=new_threshold)
        commits_after = self._repo.get_commits(
            since=self._days_to_datetime(sticky_threshold)
        )
        contributors_sticked = set()

        for commit in commits_after:
            if commit.author.login not in new:
                contributors_sticked.add(commit.author.login)

        new_contributors_count = len(new)
        if new_contributors_count == 0:
            return 0
        else:
            return len(contributors_sticked) / new_contributors_count

    def _contributor_joined_datetime(
            self, contributor: NamedUser
    ) -> Optional[datetime]:
        commits = self._repo.get_commits()
        for commit in commits.reversed:
            if commit.author == contributor:
                return commit.commit.author.date
        return None

    # not used - too much computation time
    def health(self) -> float:
        contributors = self._repo.get_contributors()
        cont_workforces = []
        for contributor in contributors:
            cont_date = self._contributor_joined_datetime(
                contributor=contributor
            )
            if not cont_date:
                raise ValueError('Some error')
            e = self.datetime_to_days(dtime=cont_date) / 30
            labor = 0.0
            j = 0
            workforce = 0.0
            since_date = cont_date
            until_date = cont_date + timedelta(days=30)
            today = datetime.now()

            commits = list(self._repo.get_commits())

            while until_date < today:
                for commit in commits:
                    added = datetime.strptime(
                        commit.last_modified, COMMIT_LAST_MODIFIED_FORMAT
                    )
                    if since_date < added < until_date:
                        additions = commit.stats.additions
                        deletions = commit.stats.deletions
                        labor += additions - deletions

                j += 1
                since_date = until_date
                until_date += timedelta(days=30)

                workforce += labor / (e - j + 1)

            cont_workforces.append(workforce)
        # return median(cont_workforces)
        return sum(cont_workforces) / len(cont_workforces)

    def wealth(self, weeks: int = 104) -> float:
        threshold_date = self.threshold_datetime(weeks=weeks)
        prs = self._repo.get_pulls(state='closed')
        relevant_prs = [pr for pr in prs if pr.created_at > threshold_date]
        wealth = 0.0
        for pr in relevant_prs:
            days_to_close = (pr.closed_at - pr.created_at).days
            if days_to_close == 0:
                days_to_close = 1
            months_to_close = ceil(days_to_close / 30)
            wealth += 1 / months_to_close
        return wealth

    def unmaintained_in_readme(self) -> bool:
        keywords_list = [
            'deprecated', 'unmaintained', 'no longer maintained',
            'no longer supported', 'no longer under development',
            'not maintained', 'not under development', 'obsolete', 'archived'
        ]
        if self.has_readme():
            readme = self._repo.get_readme().decoded_content.decode("utf-8")
            return any(keyword in readme for keyword in keywords_list)

    def in_programming_language(self) -> bool:
        repo_languages = self._repo.get_languages()
        with open('configs/languages.yml', 'r') as languages_file:
            all_languages = safe_load(languages_file)

        for repo_language in repo_languages:
            try:
                if all_languages[repo_language]['type'] == 'programming':
                    return True
            except KeyError:
                for language in all_languages:
                    if 'aliases' in all_languages[language]:
                        for alias in all_languages[language]['aliases']:
                            if (
                                alias == repo_language.lower() and
                                all_languages[language][
                                    'type'
                                ] == 'programming'
                            ):
                                return True
            return False

    def incorrectly_migrated(self) -> bool:
        commits = list(self._repo.get_commits())
        if len(commits) < 20:
            raise ValueError('Insufficient number of commits')

        files = self._get_files()
        original_size = len(files)

        for i in range(20):
            for file in commits[i].files:
                if file.status == 'added':
                    if file.filename in files:
                        files.remove(file.filename)

        new_size = len(files)
        return new_size < (original_size / 2)

    def archived(self) -> bool:
        return self._repo.archived

    def commit_in_weeks(self, weeks: int = 104) -> bool:
        threshold_date = self.threshold_datetime(weeks=weeks)
        commits = list(self._repo.get_commits(since=threshold_date))
        return bool(len(commits))

    def development_time(self) -> int:
        return (
            self.last_commit_datetime() - self.first_commit_datetime()
        ).days

    def suitable(self) -> bool:
        try:
            if self.development_time() < 730:
                return False
            if not self.in_programming_language():
                return False
            if self.incorrectly_migrated():
                return False
        except ValueError:
            return False
        return True

    def unmaintained(self) -> bool:
        return self.unmaintained_in_readme() or self.archived() or \
               not self.commit_in_weeks()

    def repo_name(self) -> str:
        return self._repo.full_name

    def url(self) -> str:
        return self._repo.html_url

    def get_row(self, features: List[str]) -> List[Any]:
        row = []
        features_len = len(features)
        feature_index = 0
        rate_limit_exceeded = False
        while feature_index < features_len:
            try:
                row.append(getattr(self, features[feature_index])())
                logger.info(
                    msg=f'Computed {feature_index + 1} / {features_len} ' +
                    f'feature: {features[feature_index]}'
                )
                rate_limit_exceeded = False
                feature_index += 1
            except RateLimitExceededException:
                if not rate_limit_exceeded:
                    rate_limit_exceeded = True
                else:
                    logger.info(
                        msg='Feature is too big to compute: ' +
                            features[feature_index]
                    )
                    row.append('Could not compute')
                    continue

                logger.info(msg='Github API rate limit reached')
                wait_for_api_calls(git=self._git)
                continue
        return row
