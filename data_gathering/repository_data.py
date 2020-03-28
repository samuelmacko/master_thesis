
from datetime import datetime
import os
from typing import Any, List, Optional

from dateutil.relativedelta import relativedelta
from github import Github
from github.GitRelease import GitRelease
from github.Repository import Repository
from github.StatsContributor import StatsContributor

_GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')


class RepositoryData:

    def __init__(self, url: str) -> None:
        self._git: Github = Github(login_or_token=_GITHUB_ACCESS_TOKEN)
        self._repo: Repository = self._git.get_repo(full_name_or_id=url)
        self.create_date: datetime.date = self._repo.created_at.date()
        self.age: int = self.get_age(date=self.create_date)
        self.contributors_raw: List[StatsContributor] = self._repo.get_stats_contributors()
        self.num_contributors: int = len(self.contributors_raw)
        self.releases_raw: List[GitRelease] = list(self._repo.get_releases())
        self.num_releases: int = len(self.releases_raw)
        self.last_release_age: int = self.get_age(
            date=self.releases_raw[0].created_at
        )
        self.last_release_downloads: int = self.release_download_count(
            release=self.releases_raw[0]
        )
        self.code_length: int = self.get_code_length()

    def relevant_cut(
            self, attribute_name: str,
            months_begin: int = 0,
            months_end: Optional[int] = None
    ) -> List[Any]:
        months_begin = self.normalize_months(months=months_begin)
        months_end = self.normalize_months(months=months_end)
        if attribute_name == 'release':
            attribute = self.releases_raw
        else:
            raise ValueError('Wrong attribute name')
        present_date = datetime.now().date()
        threshold_date = present_date - relativedelta(months=months_end)
        for i, release in enumerate(attribute):
            # TODO published_at is specific to the release, needs to be changed to something general
            if release.published_at.date() < threshold_date:
                return attribute[months_begin:i]
        return attribute[months_begin:]

    @staticmethod
    def get_age(date: datetime.date) -> int:
        present_date = datetime.now().date()
        delta = relativedelta(present_date, date)
        return delta.years * 12 + delta.months

    def normalize_months(self, months: Optional[int]) -> int:
        if months < 0:
            return 0
        if (months is None) or (months > self.age):
            months = self.age
        return months

    def releases_frequency(
            self, months_begin: int = 0, months_end: Optional[int] = None
    ) -> float:
        relevant_cut = self.relevant_cut(
            attribute_name='release', months_begin=months_begin,
            months_end=months_end
        )
        return len(relevant_cut) / (months_end - months_begin)

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
            attribute_name='release', months_begin=months_begin,
            months_end=months_end
        )
        combined_downloads = 0
        for release in relevant_cut:
            combined_downloads += self.release_download_count(release=release)
        return combined_downloads / len(relevant_cut)

    def contributors_avg_activity(
            self, num_of_weeks: Optional[int] = None
    ) -> float:
        if self.num_contributors == 0:
            raise ValueError('Repository has no contributors')
        activity = 0
        for contributor in self.contributors_raw:
            activity = self.contributor_avg_activity(
                contributor=contributor, num_of_weeks=num_of_weeks
            )
        return activity / self.num_contributors

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

    def get_code_length(self) -> int:
        # problematic languages?: shell, makefile, m4, applescript, dockerfile, ...
        length = 0
        for _, lang_length in self._repo.get_languages().items():
            length += lang_length
        return length
