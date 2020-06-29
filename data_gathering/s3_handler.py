
from datetime import datetime
from os import getenv
from time import time
from typing import List, Optional

from boto3 import client
from botocore.config import Config


_AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
_AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')


class S3Handler:

    def __init__(self, region_name: str) -> None:
        config = Config(region_name=region_name)
        self.client = client(
            's3', config=config,
            aws_access_key_id=_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=_AWS_SECRET_ACCESS_KEY
        )
        self.region = region_name

    def create_bucket(self, name: str, region: str = None) -> None:
        if region:
            location = {'LocationConstraint': region}
        else:
            location = {'LocationConstraint': self.region}

        self.client.create_bucket(
            Bucket=name, CreateBucketConfiguration=location
        )

    def bucket_exits_check(self, bucket_name: str) -> bool:
        try:
            self.client.list_objects(Bucket=bucket_name)
            return True
        except self.client.exceptions.NoSuchBucket:
            return False

    def upload_file(self, file_name: str, bucket_name: str) -> None:
        object_name_ts = self.append_time_stamp(s=file_name)
        self.client.upload_file(file_name, bucket_name, object_name_ts)

    def delete_oldest_object_with_prefix(
        self, prefix: str, bucket_name: str
    ) -> None:
        """Deletes oldest object in the bucket which starts with the prefix.

        Oldest object is determined by the timestamp in the object name.
        Object will not be deleted if it is the only object with the given
        prefix in the bucket.

        Args:
            file_name: Name of the file to be uploaded.
            bucket_name: Name of the bucket to which should file by uploaded
        """
        file_tuples_list = [
            (obj_name, self.extract_time_stamp(s=obj_name))
            for obj_name in self.list_objects_in_bucket(
                bucket_name=bucket_name
            )
            if obj_name.startswith(prefix)
        ]
        if len(file_tuples_list) > 0:
            file_tuples_list.sort(key=lambda tup: tup[1])
            self.client.delete_object(
                Bucket=bucket_name, Key=file_tuples_list[0][0]
            )

    def download_file(
        self, file_name: str, bucket_name: str, object_name: str
    ) -> None:
        with open(file_name, 'wb') as f:
            self.client.download_fileobj(bucket_name, object_name, f)

    def list_objects_in_bucket(self, bucket_name: str) -> List[Optional[str]]:
        return [
            obj['Key'] for obj in self.client.list_objects(
                Bucket=bucket_name
            )['Contents']
        ]

    @staticmethod
    def append_time_stamp(s: str) -> str:
        current_time = time()
        time_stamp = datetime.fromtimestamp(current_time).strftime(
            '%Y/%m/%d_%H:%M:%S'
        )
        return s + '-' + time_stamp

    @staticmethod
    def extract_time_stamp(s: str) -> datetime:
        time_stamp = s[s.rfind('-') + 1:]
        return datetime.strptime(time_stamp, '%Y/%m/%d_%H:%M:%S')
