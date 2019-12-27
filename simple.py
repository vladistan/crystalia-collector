import os


def file_len(name):
    return os.stat(name).st_size
