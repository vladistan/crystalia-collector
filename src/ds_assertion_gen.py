import uuid as uuid
from src import crystalia_ns as crys
from readers import obfuscate_filename


def get_assertions_from_brace_triples(braces_stream, ds):

    yield (ds, 'a', crys.DATASET)
    yield (ds, crys.RDF_TYPE, crys.DATASET)

    for t in braces_stream:
        yield from brace_to_rdf_triple(t, ds)


def index_ds_assertions(triples):
    index = {}

    def update_index(key, value):
        if key not in index or index[key] == value:
            index[key] = value
        else:
            v = index[key]
            if isinstance(v, set):
                index[key] |= {value}
            else:
                index[key] = {index[key], value}

    for t in triples:
        update_index(('po', t[1], t[2]), t[0])
        update_index(('sp', t[0], t[1]), t[2])

    return index


name_idx = {}


def dereify_by_id(idx, stmt_id):
    m = idx[('sp', stmt_id, crys.HAS_METHOD)]
    a = idx[('sp', stmt_id, crys.HAS_ARGUMENT)]
    v = idx[('sp', stmt_id, crys.HAS_VALUE)]
    c = idx[('sp', stmt_id, crys.HAS_COVER)]

    return m, a, v, c


def dereify_method(idx, assertions, method):
    for a in assertions:
        (m, args, value, cov) = dereify_by_id(idx, a)
        if m == method:
            return args, value, cov


def q(s):
    return '"' + s + '"'


def brace_to_rdf_triple(bt, ds):

    fname = bt[0]
    if fname not in name_idx:
        obj_id = uniq_obj_id()
        name_idx[fname] = obj_id
    else:
        obj_id = name_idx[fname]

    yield (obj_id, 'a', crys.FILE_ARTIFACT)
    yield (obj_id, crys.RDF_TYPE, crys.FILE_ARTIFACT)
    yield (obj_id, crys.FILE_NAME, q(fname))
    yield (obj_id, crys.NAME_HASH, q(obfuscate_filename(fname)))
    yield (ds, crys.HAS_OBJECT, obj_id)

    method = bt[1]

    st_id = uniq_obj_id()

    if method == 'len':

        yield (obj_id, crys.HAS_ASSERTION, st_id)
        yield (obj_id, 'a', crys.ASSERTION)
        yield (obj_id, crys.RDF_TYPE, crys.ASSERTION)

        yield (st_id, crys.HAS_METHOD, crys.METHOD_LEN)
        yield (st_id, crys.HAS_VALUE, int(bt[2]))
        yield (st_id, crys.HAS_ARGUMENT, q('nil'))
        yield (st_id, crys.HAS_COVER, 1.0)

    elif method == 'md5':

        yield (obj_id, crys.HAS_ASSERTION, st_id)
        yield (obj_id, 'a', crys.ASSERTION)
        yield (obj_id, crys.RDF_TYPE, crys.ASSERTION)

        yield (st_id, crys.HAS_METHOD, crys.METHOD_FULL_MD5)
        yield (st_id, crys.HAS_VALUE, q(bt[2]))
        yield (st_id, crys.HAS_ARGUMENT, q('nil'))
        yield (st_id, crys.HAS_COVER, 1.0)


def uniq_obj_id():
    obj_id = 'urn:{}'.format(str(uuid.uuid1()))
    return obj_id
