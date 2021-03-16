
from datetime import datetime
from logging import Logger
from os import getenv
from time import time
from typing import List, Optional

from boto3 import client
from botocore.config import Config


_AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
_AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
_BUCKET_NAME = getenv('BUCKET_NAME')
_ENDPOINT_URL = getenv('ENDPOINT_URL')

_TIMESTAMP_FORMAT = '%Y-%m-%d-%H:%M:%S'


class S3Handler:

    def __init__(self, region_name: str) -> None:
        config = Config(region_name=region_name)
        self.client = client(
            's3', config=config,
            aws_access_key_id=_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=_AWS_SECRET_ACCESS_KEY,
            endpoint_url=_ENDPOINT_URL
        )
        self.region = region_name

    def create_bucket(self, region: str = None) -> None:
        if region:
            location = {'LocationConstraint': region}
        else:
            location = {'LocationConstraint': self.region}

        self.client.create_bucket(
            Bucket=_BUCKET_NAME, CreateBucketConfiguration=location
        )

    def bucket_exits_check(self) -> bool:
        try:
            self.client.list_objects(Bucket=_BUCKET_NAME)
            return True
        except self.client.exceptions.NoSuchBucket:
            return False

    def upload_file(
        self, file_name: str, logger: Logger, prefix: str = ''
    ) -> None:
        object_name_ts = self.append_time_stamp(s=file_name)
        self.client.upload_file(
            file_name, _BUCKET_NAME, prefix + object_name_ts
        )
        logger.debug(msg=f'File uploaded: {object_name_ts}, prefix: {prefix}')

    def delete_oldest_object(
        self, file_name: str, logger: Logger, prefix: str = ''
    ) -> None:
        """Deletes oldest object in the bucket with given file name.

        Oldest object is determined by the timestamp in the object name.
        Object will not be deleted if it is the only object with the given
        prefix in the bucket.

        Args:
            file_name: Name of the file to be uploaded.
        """
        file_tuples_list = [
            (obj_name, self.extract_time_stamp(s=obj_name))
            for obj_name in self.list_objects_in_bucket(prefix=prefix)
            if self.remove_prefix(
                s=obj_name, prefix=prefix
            ).startswith(file_name)
        ]
        logger.debug(
            msg=f'Old files found: {[f[0] for f in file_tuples_list]}'
        )
        if len(file_tuples_list) > 1:
            file_tuples_list.sort(key=lambda tup: tup[1])
            oldest_object = file_tuples_list[0][0]
            response = self.client.delete_object(
                Bucket=_BUCKET_NAME, Key=oldest_object
            )
            logger.debug(
                msg=f'File deleted: {oldest_object}, response code: ' +
                    f'{response["ResponseMetadata"]["HTTPStatusCode"]}'
            )
            logger.debug(msg=f'Full responose: {response["ResponseMetadata"]}')

    def download_file(
        self, file_name: str, logger: Logger, object_name: str = None,
        prefix: str = ''
    ) -> None:
        obj_to_download = None
        if object_name:
            obj_to_download = object_name
        else:
            bucket_objs = self.list_objects_in_bucket(prefix=prefix)
            for bucket_obj in bucket_objs:
                obj_name_without_prefix = self.remove_prefix(
                    s=bucket_obj, prefix=prefix
                )
                if obj_name_without_prefix.startswith(file_name):
                    obj_to_download = bucket_obj

        if obj_to_download:
            with open(file_name, 'wb') as f:
                self.client.download_fileobj(_BUCKET_NAME, obj_to_download, f)
            logger.debug(msg=f'File downloaded: {obj_to_download}')
        else:
            logger.debug(msg='No file to download found')
            # todo raise some exception if file does not exist
            pass

    def list_objects_in_bucket(self, prefix: str = '') -> List[Optional[str]]:
        try:
            return [
                obj['Key'] for obj in self.client.list_objects(
                    Bucket=_BUCKET_NAME, Prefix=prefix
                )['Contents']
            ]
        except KeyError:
            return []

    @staticmethod
    def append_time_stamp(s: str) -> str:
        current_time = time()
        time_stamp = datetime.fromtimestamp(current_time).strftime(
            _TIMESTAMP_FORMAT
        )
        return s + '_' + time_stamp

    @staticmethod
    def extract_time_stamp(s: str) -> datetime:
        time_stamp = s[s.rfind('_') + 1:]
        return datetime.strptime(time_stamp, _TIMESTAMP_FORMAT)

    @staticmethod
    def remove_time_stamp(s: str) -> str:
        return s[:s.rfind('_')]

    @staticmethod
    def remove_prefix(s: str, prefix: str) -> str:
        return s[len(prefix):]
