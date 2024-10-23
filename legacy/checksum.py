import hashlib


def md5_checksum(file):
    with open(file, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
