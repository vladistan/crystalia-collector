import boto3
from typing import Iterator

from dataclasses import dataclass
from datetime import datetime

@dataclass
class S3Object:
    key: str
    last_modified: datetime
    etag: str
    size: int

def s3_object_from_dict(obj: dict) -> S3Object:
    return S3Object(
        key=obj['Key'],
        last_modified=obj['LastModified'],
        etag=obj['ETag'],
        size=obj['Size']
    )

def list_files_in_s3_prefix(bucket_name: str, prefix: str) -> Iterator[S3Object]:
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    
    for obj in response['Contents']:
        yield s3_object_from_dict(obj)
    while response['IsTruncated']:
        response = s3.list_objects_v2(
            Bucket=bucket_name, 
            Prefix=prefix, 
            ContinuationToken=response['NextContinuationToken'])
        for obj in response['Contents']:
            yield s3_object_from_dict(obj)

