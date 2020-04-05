
from .enums import Attributes

from datetime import datetime
import os
from typing import Any, List, Optional

from dateutil.relativedelta import relativedelta
from github import Github
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.StatsContributor import StatsContributor

_GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')


class RepositoryData:

    def __init__(self, url: str) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)
        self._repo: Repository = self._git.get_repo(full_name_or_id=url)
        self._issues_raw: List[Issue] = list(self._repo.get_issues())
        self._contributors_raw: List[StatsContributor] = self._repo.get_stats_contributors()
        self._releases_raw: List[GitRelease] = list(self._repo.get_releases())
        self._pulls_raw: List[PullRequest] = list(
            self._repo.get_pulls(state='closed')
        )
        self._create_date: datetime.date = self._repo.created_at.date()
        self.age: int = self.get_age(date=self._create_date)
        self.size: int = self._repo.size
        self.pull_last_age: int = self.get_age(
            date=self._pulls_raw[0].created_at
        )
        self.contributors_count: int = len(self._contributors_raw)

    def issues_ration(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.ISSUES, months_begin=months_begin,
            months_end=months_end
        )
        opened_count = closed_count = 0
        for issue in relevant_cut:
            opened_count += issue.state == 'opened'
            closed_count += issue.state == 'closed'
        return opened_count / closed_count

    def issues_avg_close_time(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.ISSUES, months_begin=months_begin,
            months_end=months_end
        )
        total_time_to_close = 0
        for issue in relevant_cut:
            delta = issue.closed_at - issue.created_at
            total_time_to_close += delta.total_seconds() / 3600
        return total_time_to_close / len(relevant_cut)

    def issues_avg_close_count(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.ISSUES, months_begin=months_begin,
            months_end=months_end
        )
        count = 0
        for issue in relevant_cut:
            count += issue.state == 'closed'
        return count / len(relevant_cut)

    def pulls_avg_close_time(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.PULLS, months_begin=months_begin,
            months_end=months_end
        )
        total_time_to_close = 0
        for pull in relevant_cut:
            delta = pull.closed_at - pull.created_at
            total_time_to_close += delta.total_seconds() / 3600
        return total_time_to_close / len(relevant_cut)

    def pulls_avg_close_count(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.PULLS, months_begin=months_begin,
            months_end=months_end
        )
        count = 0
        for pull in relevant_cut:
            count += pull.state == 'closed'
        return count / len(relevant_cut)

    def pulls_avg_addition(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.PULLS, months_begin=months_begin,
            months_end=months_end
        )
        total_addition = 0.0
        for pull in relevant_cut:
            total_addition += pull.additions - pull.deletions
        return total_addition / len(relevant_cut)

    def attribute_count(
            self, attribute_name: str, months_begin: int = 0,
            months_end: Optional[int] = None
    ) -> int:
        relevant_cut = self.relevant_cut(
            attribute=attribute_name, months_begin=months_begin,
            months_end=months_end
        )
        return len(relevant_cut)

    def attribute_frequency(
            self, attribute_name: str, months_begin: int = 0,
            months_end: Optional[int] = None
    ) -> float:
        count = self.attribute_count(
            attribute_name=attribute_name, months_begin=months_begin,
            months_end=months_end
        )
        return count / (months_end - months_begin)

    @staticmethod
    def release_download_count(release: GitRelease) -> int:
        downloads = 0
        for asset in release.get_assets():
            downloads += asset.download_count
        return downloads

    def releases_avg_download_count(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute=Attributes.RELEASES, months_begin=months_begin,
            months_end=months_end
        )
        combined_downloads = 0
        for release in relevant_cut:
            combined_downloads += self.release_download_count(release=release)
        return combined_downloads / len(relevant_cut)

    def release_last_age(self) -> int:
        return self.get_age(
            date=self._repo.get_latest_release().created_at
        )

    def release_last_downloads(self) -> int:
        return self.release_download_count(
            release=self._repo.get_latest_release()
        )

    def relevant_cut(
            self, attribute: Attributes,
            months_begin: int = 0,
            months_end: Optional[int] = None
    ) -> List[Any]:
        """
        Get only relevant objects (e.g. pulls, issues, releases)

        Args:
            attribute {Attribute} -- type of attribute (e.g. pulls, issues, releases)
            months_begin {int} -- how many months back to start the slice
            months_end {int} -- how many months back to end the slice

        Returns:
            List[Any] -- slice of relevant objects
        """
        months_begin = self.normalize_months(months=months_begin)
        months_end = self.normalize_months(months=months_end)
        present_date = datetime.now().date()
        threshold_date = present_date - relativedelta(months=months_end)
        for i, att in enumerate(attribute[0]):
            if getattr(att, attribute[1]).date() < threshold_date:
                return attribute[months_begin:i]
        return attribute[months_begin:]

    @staticmethod
    def get_age(date: datetime.date) -> int:
        """
        Convert date in datetime.date to age in months

        Args:
            date {datetime.date} -- date

        Returns:
            int -- age in months
        """
        present_date = datetime.now().date()
        delta = relativedelta(present_date, date)
        return delta.years * 12 + delta.months

    def normalize_months(self, months: Optional[int]) -> int:
        if (months is None) or (months > self.age):
            return self.age
        elif months < 0:
            return 0

    def contributors_avg_activity(
            self, num_of_weeks: Optional[int] = None
    ) -> float:
        if self.contributors_count == 0:
            raise ValueError('Repository has no contributors')
        activity = 0
        for contributor in self._contributors_raw:
            activity = self.contributor_avg_activity(
                contributor=contributor, num_of_weeks=num_of_weeks
            )
        return activity / self.contributors_count

    @staticmethod
    def contributor_avg_activity(
            contributor: StatsContributor,
            num_of_weeks: Optional[int] = None
    ) -> float:
        # additions = deletions = commits = 0
        additions = deletions = 0
        for week in contributor.weeks[:num_of_weeks]:
            data = week.raw_data
            additions += data['a']
            deletions += data['d']
            # commits += data['c']
        if num_of_weeks is None:
            num_of_weeks = len(contributor.weeks)
        return (additions + deletions) / num_of_weeks

    def code_length(self) -> int:
        length = 0
        for _, lang_length in self._repo.get_languages().items():
            length += lang_length
        return length

    def watchers_count(self) -> int:
        return self._repo.watchers_count

    def forks_count(self) -> int:
        return self._repo.forks_count

    def stargazers_count(self) -> int:
        return self._repo.stargazers_count
