"""NFR benchmarks for Phase 6.3 (CRYSTALIA-COLLECTOR-01 comprehensive-enhancement).

Skipped by default. Run explicitly with:

    uv run pytest -m benchmark -v -s

Targets (from plan Step 6.3):
- Local listing of 10,000 files < 5.0 s
- Single-file glimpse descriptor build < 100 ms
- run_pipeline over 1,000 files with peak memory delta < 500 MB
  (plan target was 100K; 1K sample used per plan clause "or 1K")
"""

from __future__ import annotations

import time
import tracemalloc
from pathlib import Path

import pytest

from crystalia_collector.glimpse_compute import build_file_descriptor
from crystalia_collector.method.glimpse import Glimpse
from crystalia_collector.source.local import LocalSource
from crystalia_collector.work import run_pipeline

pytestmark = pytest.mark.benchmark

_LISTING_FILES = 10_000
_LISTING_SLA_SECONDS = 5.0
_GLIMPSE_FILE_BYTES = 4 * 1024
_GLIMPSE_SLA_SECONDS = 0.100
_PIPELINE_FILES = 1_000
_PIPELINE_FILE_BYTES = 100
_PIPELINE_MEMORY_SLA_BYTES = 500 * 1024 * 1024


def _make_files(root: Path, count: int, size: int) -> None:
    payload = b"x" * size if size > 0 else b""
    for i in range(count):
        (root / f"f_{i:07d}.dat").write_bytes(payload)


def test_nfr_local_listing_10k_files_under_5s(tmp_path: Path) -> None:
    _make_files(tmp_path, _LISTING_FILES, 0)

    source = LocalSource()
    start = time.perf_counter()
    count = sum(1 for _ in source.list_files(str(tmp_path)))
    elapsed = time.perf_counter() - start

    print(f"\n[NFR] local listing {count} files: {elapsed:.3f}s (SLA <{_LISTING_SLA_SECONDS}s)")
    assert count == _LISTING_FILES
    assert elapsed < _LISTING_SLA_SECONDS


def test_nfr_single_file_glimpse_under_100ms(tmp_path: Path) -> None:
    target = tmp_path / "sample.dat"
    target.write_bytes(bytes(range(256)) * (_GLIMPSE_FILE_BYTES // 256))

    source = LocalSource()
    file_obj = next(source.list_files(str(tmp_path)))
    method = Glimpse()

    start = time.perf_counter()
    top, children = build_file_descriptor(file_obj, method, source)
    elapsed = time.perf_counter() - start

    print(f"\n[NFR] single-file glimpse: {elapsed * 1000:.2f}ms (SLA <{_GLIMPSE_SLA_SECONDS * 1000:.0f}ms)")
    assert top is not None
    assert children
    assert elapsed < _GLIMPSE_SLA_SECONDS


def test_nfr_run_pipeline_1k_files_under_500mb(tmp_path: Path) -> None:
    # Plan target: 100K files. Per plan clause "or 1K", we use 1K here for CI-friendly runtime;
    # peak-memory SLA remains 500 MB (delta) as an upper bound with substantial headroom.
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    _make_files(input_dir, _PIPELINE_FILES, _PIPELINE_FILE_BYTES)
    output_path = tmp_path / "out.ttl"

    tracemalloc.start()
    try:
        result = run_pipeline(
            prefix=str(input_dir),
            method_ids=["glimpse"],
            output_path=output_path,
            workers=2,
            fmt="turtle",
        )
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    print(
        f"\n[NFR] run_pipeline {_PIPELINE_FILES} files, peak={peak / (1024 * 1024):.1f}MB "
        f"(SLA <{_PIPELINE_MEMORY_SLA_BYTES // (1024 * 1024)}MB)"
    )
    assert result.succeeded == _PIPELINE_FILES
    assert output_path.exists()
    assert peak < _PIPELINE_MEMORY_SLA_BYTES
