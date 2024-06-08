import os

from src.checksum import md5_checksum
from src.collector import filename_collector


def file_len(name):
    return os.stat(name).st_size


def collect_dataset_metrics(path):
    names = filename_collector(path)

    for name in names:
        fpath = os.path.join(path, name)
        yield (name, 'len', file_len(fpath))
        yield (name, 'md5', md5_checksum(fpath))
