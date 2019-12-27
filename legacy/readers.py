import re
import hashlib
import uuid


def remove_quotes(token):
    if token[0] == '\'':
        return token[1:-1]
    return token


def obfuscate_filename(name):
    return hashlib.md5(name.encode('utf-8')).hexdigest()[0:10]


def braces_reader(stream):
    triple_re = re.compile(r'^\((.+),[\s]*(.+),[\s]*(.+)\)$')

    for line in stream:

        if line[:-1] == '\n':
            line = line[:-1]

        if line == '':
            continue

        triple = triple_re.match(line)

        if triple is None:
            continue

        triple = triple.groups()
        triple = tuple(remove_quotes(token) for token in triple)

        yield triple
