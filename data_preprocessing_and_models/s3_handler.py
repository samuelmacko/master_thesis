
from logging import Logger
from os import getenv
from typing import Optional

from boto3 import client
from botocore.config import Config


_AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
_AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
_BUCKET_NAME = getenv('BUCKET_NAME')
_ENDPOINT_URL = getenv('ENDPOINT_URL')


class S3Handler:

    def __init__(self, region_name: str) -> None:
        config = Config(region_name=region_name)
        self.client = client(
            's3', config=config,
            aws_access_key_id=_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=_AWS_SECRET_ACCESS_KEY,
            endpoint_url=_ENDPOINT_URL
        )

    def upload_file(
            self, file_name: str, log: Logger, prefix: Optional[str] = None
    ) -> None:
        log.info(msg='Started uploading file: ' + file_name)
        if not prefix:
            prefix = ''
        self.client.upload_file(
            file_name, _BUCKET_NAME, prefix + file_name
        )
        log.debug(msg=f'File successfully uploaded: {file_name}, prefix: {prefix}')
