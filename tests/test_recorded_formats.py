"""Deterministic output over tests/recorded/formats/ (DM v2 plan, Phase 7 Steps 7.3-7.6).

Same determinism contract as test_recorded.py, over a separate fixture tree that
carries a zip file (Phase 2's tree/ fixture has none, and adding one there would
change every other method's already-recorded fixture).
"""

import os
import shutil
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from crystalia_collector.work import run_pipeline

FIXTURE_TREE = Path(__file__).parent / "recorded" / "formats"
RECORDED_DIR = Path(__file__).parent / "recorded"
_PINNED_TIMESTAMP = 1704067200.0  # 2024-01-01T00:00:00Z
_PINNED_CLOCK = datetime(2024, 1, 1, tzinfo=UTC)
_PINNED_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
_PINNED_SOURCE_ROOT = "/recorded/fixture/formats"


def _pinned_clock() -> datetime:
    return _PINNED_CLOCK


class _PinnedStat:
    """Wraps a real os.stat_result, pinning only mtime/ctime; everything else passes through."""

    def __init__(self, real: os.stat_result) -> None:
        self._real = real
        self.st_mtime = _PINNED_TIMESTAMP
        self.st_ctime = _PINNED_TIMESTAMP

    def __getattr__(self, name: str):
        return getattr(self._real, name)


def _deterministic_id_factory() -> Callable[[], str]:
    counter = iter(range(1, 100_000))

    def factory() -> str:
        return f"crys:recorded-item-{next(counter):04d}"

    return factory


@pytest.fixture(autouse=True)
def _pin_filesystem_times(monkeypatch):
    real_stat = os.stat

    def pinned_stat(path, *args, **kwargs):  # noqa: ANN001 - matches os.stat's signature
        return _PinnedStat(real_stat(path, *args, **kwargs))

    monkeypatch.setattr(os, "stat", pinned_stat)


@pytest.fixture(autouse=True)
def _pin_harvest_uuid(monkeypatch):
    monkeypatch.setattr("crystalia_data_model.types.provenance.uuid4", lambda: _PINNED_UUID)


def _prepare_tree(tmp_path: Path) -> Path:
    dest = tmp_path / "formats"
    shutil.copytree(FIXTURE_TREE, dest)
    return dest.resolve()


_METHODS = ["bookend", "bookend-dir", "zip-cd", "zip-manifest"]
_RECORDED_NAMES = [(m, f"{m}.ttl") for m in _METHODS]


@pytest.mark.parametrize("method", _METHODS)
def test_two_runs_produce_byte_identical_ttl(tmp_path, method):
    tree = _prepare_tree(tmp_path)
    out1, out2 = tmp_path / "out1.ttl", tmp_path / "out2.ttl"

    for out in (out1, out2):
        run_pipeline(
            str(tree),
            [method],
            out,
            workers=1,
            fmt="turtle",
            item_id_factory=_deterministic_id_factory(),
            clock=_pinned_clock,
            source_root=_PINNED_SOURCE_ROOT,
        )

    assert out1.read_bytes() == out2.read_bytes()


@pytest.mark.parametrize(("method", "recorded_name"), _RECORDED_NAMES)
def test_run_matches_recorded_fixture_byte_for_byte(tmp_path, method, recorded_name):
    tree = _prepare_tree(tmp_path)
    out = tmp_path / "out.ttl"

    run_pipeline(
        str(tree),
        [method],
        out,
        workers=1,
        fmt="turtle",
        item_id_factory=_deterministic_id_factory(),
        clock=_pinned_clock,
        source_root=_PINNED_SOURCE_ROOT,
    )

    assert out.read_bytes() == (RECORDED_DIR / recorded_name).read_bytes()


def _write_recorded() -> None:  # pragma: no cover - manual regeneration helper
    """Regenerate the recorded fixtures. Run only on an intentional change; review the diff."""
    import tempfile

    for method, recorded_name in _RECORDED_NAMES:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tree = _prepare_tree(tmp_path)
            out = tmp_path / "out.ttl"
            run_pipeline(
                str(tree),
                [method],
                out,
                workers=1,
                fmt="turtle",
                item_id_factory=_deterministic_id_factory(),
                clock=_pinned_clock,
                source_root=_PINNED_SOURCE_ROOT,
            )
            (RECORDED_DIR / recorded_name).write_bytes(out.read_bytes())


if __name__ == "__main__":  # pragma: no cover
    if os.environ.get("CRYSTALIA_REGEN_RECORDED") == "1":
        import unittest.mock

        real_stat = os.stat

        def _pinned(path: object, *a: object, **kw: object) -> _PinnedStat:
            return _PinnedStat(real_stat(path, *a, **kw))  # type: ignore[arg-type]

        with (
            unittest.mock.patch("os.stat", new=_pinned),
            unittest.mock.patch("crystalia_data_model.types.provenance.uuid4", new=lambda: _PINNED_UUID),
        ):
            _write_recorded()
