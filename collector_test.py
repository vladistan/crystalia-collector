import os

from collector import filename_collector
from checksum import md5_checksum
from simple import file_len, collect_dataset_metrics

dir_path = os.path.dirname(os.path.realpath(__file__))
ds_path = os.path.join(dir_path, 'test_fixtures/simple_ds1')


def test_that_file_objs_streams_all_names():
    name_stream = filename_collector(ds_path)
    combined = [n for n in name_stream]
    assert 'lorem_inst.txt' in combined


def test_that_we_can_get_md5_of_a_file():
    chesksum = md5_checksum(f'{ds_path}/ch2/ch2a.txt')
    assert chesksum == '4b81c8954db4aff4727bbab124bd73ba'


def test_that_we_can_get_len_of_a_file():
    flen = file_len(f'{ds_path}/ch2/ch2a.txt')
    assert flen == 1479


def test_simple_collector():
    metrics = collect_dataset_metrics(ds_path)
    combined = [n for n in metrics]

    assert ('ch2/ch2a.txt', 'len', 1479) in combined
    assert ('ch2/ch2a.txt', 'md5', '4b81c8954db4aff4727bbab124bd73ba') in combined
