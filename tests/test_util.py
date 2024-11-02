from datetime import datetime

import pytest

from crystalia_collector.method.md5 import MD5_2GB
from crystalia_collector.s3_iface import S3Object
from crystalia_collector.util import human_readable_size, stream_offsets, process_file


def test_human_readable_size_bytes_less_than_1_kb():
  assert human_readable_size(500) == "500"
  assert human_readable_size(1023) == "1023"


def test_human_readable_size_exactly_1_kb():
  assert human_readable_size(1024) == "1.0 KB"


def test_human_readable_size_between_1_kb_and_1_pb():
  assert human_readable_size(2048) == "2.0 KB"
  assert human_readable_size(15360) == "15.0 KB"

  assert human_readable_size(2 ** 20) == "1.0 MB"
  assert human_readable_size(5 * 2 ** 20) == "5.0 MB"
  assert human_readable_size(50 * 2 ** 20) == "50.0 MB"
  assert human_readable_size(2 ** 30) == "1.0 GB"
  assert human_readable_size(3 * 2 ** 30) == "3.0 GB"
  assert human_readable_size(10 * 2 ** 30) == "10.0 GB"
  assert human_readable_size(3 * 2 ** 40) == "3.0 TB"
  assert human_readable_size(10 * 2 ** 40) == "10.0 TB"
  assert human_readable_size(3 * 2 ** 40) == "3.0 TB"
  assert human_readable_size(10 * 2 ** 40) == "10.0 TB"
  assert human_readable_size(3 * 2 ** 50) == "3.0 PB"
  assert human_readable_size(10 * 2 ** 50) == "10.0 PB"


def test_human_readable_size_zero_bytes():
  assert human_readable_size(0) == "0"


def test_human_readable_size_negative_size():
  assert human_readable_size(-1024) == "-1024"


def test_generate_offsets_normal_case():
  offsets = list(stream_offsets(1024, 4096))
  assert offsets == [0, 1024, 2048, 3072]


def test_generate_offsets_length_not_multiple_of_blocksize():
  offsets = list(stream_offsets(1000, 3500))
  assert offsets == [0, 1000, 2000, 3000]


def test_generate_offsets_length_zero():
  offsets = list(stream_offsets(1000, 0))
  assert offsets == []


def test_generate_offsets_blocksize_greater_than_length():
  offsets = list(stream_offsets(5000, 2000))
  assert offsets == [0]


def test_generate_offsets_zero_blocksize():
  with pytest.raises(ValueError):
    list(stream_offsets(0, 1000))


def test_generate_offsets_negative_length():
  offsets = list(stream_offsets(1000, -2000))
  assert offsets == []


def test_generate_offsets_for_large_file():
  gb = 2 ** 30
  offsets = list(stream_offsets(8 * gb, 35 * gb))
  assert offsets == [0, 8 * gb, 16 * gb, 24 * gb, 32 * gb]


def test_process_file(work_dir):

  file = S3Object(
      key='data/bob.tgz',
      last_modified=datetime(2021, 1, 1),
      etag='1234567890',
      size=5 * 2 ** 30)

  md5_2gb = MD5_2GB()

  small_files = []
  process_file(file=file,
             bucket='1000genomes-dragen-v4.0.3',
             task_dir=work_dir,
             method=md5_2gb,
             task_num=1,
             small_files=small_files,
             )
