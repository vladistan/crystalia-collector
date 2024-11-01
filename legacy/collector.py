import os


def filename_collector(path):
    for dirName, subdirList, fileList in os.walk(path, topdown=False):
        for fname in fileList:
            yield os.path.join(dirName, fname)[len(path) + 1:]
