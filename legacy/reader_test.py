import os

from ds_assertion_gen import get_assertions_from_brace_triples, index_ds_assertions, brace_to_rdf_triple, dereify_method
from readers import braces_reader, obfuscate_filename
import crystalia_ns as crys

dir_path = os.path.dirname(os.path.realpath(__file__))
fixtures_path = os.path.join(dir_path, 'test_fixtures')
fixture_file_name = os.path.join(fixtures_path, 'braces_summary.txt')


def test_that_we_can_read_braces_triples():
    with open(fixture_file_name, 'r') as stream:
        braces_stream = braces_reader(stream)
        combined = [n for n in braces_stream]
        assert len(combined) == 4
        assert ('f1.data', 'len', '11878400') in combined
        assert ('f1.data', 'md5', 'ab2be597331179aba734c0876ee06e63') in combined


def test_obfuscate_filename():
    assert obfuscate_filename('f1.data') == 'baaca37882'


def test_index_by_subj_predicate():
    triples = (
        (1, 2, 3),
        (3, 2, 3),
        (3, 3, 2),
        ('cat', 'dog', 'bill'),
        (12, 'dog', 'man'),
        ('cat', 12, 'man'),
        ('cat', 12, 'dog'),
        (7, 12, 'jim'),
        ('dog', 12, 'jim'),

        ('cat', 'dog', 'bill'),
        (55, 'dog', 'bill'),
        ('rat', 'dog', 'bill'),

    )

    po_index = index_ds_assertions(triples)

    assert po_index[('sp', 1, 2)] == 3
    assert po_index[('sp', 'cat', 'dog')] == 'bill'
    assert po_index[('sp', 'rat', 'dog')] == 'bill'
    assert po_index[('sp', 'cat', 12)] == {'man', 'dog'}


def test_index_by_predicate_obj_with_multi():
    triples = (
        (1, 2, 3),
        (3, 2, 3),
        (3, 3, 2),
        ('cat', 'dog', 'bill'),
        (12, 'dog', 'man'),
        ('cat', 12, 'man'),
        (7, 12, 'jim'),
        ('dog', 12, 'jim'),

        ('cat', 'dog', 'bill'),
        (55, 'dog', 'bill'),
        ('rat', 'dog', 'bill'),

    )

    po_index = index_ds_assertions(triples)

    assert po_index[('po', 2, 3)] == {1, 3}
    assert po_index[('po', 3, 2)] == 3

    assert po_index[('po', 12, 'jim')] == {7, 'dog'}


def test_index_by_predicate_obj_all_singular():
    triples = (
        (1, 2, 3),
        (3, 4, 5),
        (3, 3, 2),
        ('cat', 'dog', 'bill'),
        (12, 'dog', 'man'),
        ('cat', 12, 'man'),
        ('cat', 12, 12)
    )

    po_index = index_ds_assertions(triples)

    assert po_index[('po', 2, 3)] == 1
    assert po_index[('po', 4, 5)] == 3
    assert po_index[('po', 3, 2)] == 3

    assert po_index[('po', 'dog', 'bill')] == 'cat'
    assert po_index[('po', 12, 'man')] == 'cat'
    assert po_index[('po', 12, 12)] == 'cat'


def test_brace_to_rdf_converts_name_correctly():
    brace_triples = ('f1.data', 'len', '11878400')

    rdf = brace_to_rdf_triple(brace_triples, 'urn:crystalia:unit-test-01')
    po_index = index_ds_assertions(rdf)

    assert ('po', crys.FILE_NAME, '"f1.data"') in po_index


def test_rdf_triples():
    ds = 'urn:crystalia:obj:unit-test-rdf-01'

    with open(fixture_file_name, 'r') as stream:
        braces_stream = braces_reader(stream)
        ds_assertions = get_assertions_from_brace_triples(braces_stream, ds)

        coll = [t for t in ds_assertions]
        po_index = index_ds_assertions(coll)

        assert ('po', crys.FILE_NAME, '"f1.data"') in po_index
        assert ('po', crys.NAME_HASH, '"baaca37882"') in po_index

        objId = po_index[('po', crys.FILE_NAME, '"f1.data"')]
        assertions = po_index[('sp', objId, crys.HAS_ASSERTION)]

        assert len(assertions) == 2

        (args, value, cov) = dereify_method(po_index, assertions, crys.METHOD_LEN)
        assert value == 11878400

        (args, value, cov) = dereify_method(po_index, assertions, crys.METHOD_FULL_MD5)
        assert value == '"ab2be597331179aba734c0876ee06e63"'
