"""Deterministic output over tests/recorded/tree/ (DM v2 plan, Phase 2 Step 2.3).

Two runs over the fixture tree must produce byte-identical TTL, and a run must
match the recorded tests/recorded/<method>.ttl exactly. Real filesystem mtime
and ctime are not otherwise reproducible across machines/checkouts, so both are
pinned via a monkeypatched os.stat for the duration of each test.

To regenerate a recorded fixture after an intentional change: run this file's
`_prepare_tree` + `run_pipeline` with the deterministic id factory by hand (see
`_write_recorded` below, invoked only when CRYSTALIA_REGEN_RECORDED=1 is set),
inspect the diff, and commit it as a reviewed change.
"""

import os
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from crystalia_collector.work import run_pipeline

FIXTURE_TREE = Path(__file__).parent / "recorded" / "tree"
RECORDED_DIR = Path(__file__).parent / "recorded"
_PINNED_TIMESTAMP = 1704067200.0  # 2024-01-01T00:00:00Z


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


def _prepare_tree(tmp_path: Path) -> Path:
    # Resolved: FileObject.uri is always path.resolve()'d in LocalSource, so the
    # root prefix must match that form or _ancestor_uris' length comparison drifts.
    dest = tmp_path / "tree"
    shutil.copytree(FIXTURE_TREE, dest)
    return dest.resolve()


_METHODS = [
    "glimpse",
    "glimpse-slim",
    "glimpse-light",
    "glimpse-meta",
    "glimpse-dir",
    "glimpse-dir-slim",
    "glimpse-dir-light",
    "glimpse-dir-meta",
    "md5",
]

_RECORDED_NAMES = [(m, f"{m}.ttl") for m in _METHODS]


@pytest.mark.parametrize("method", _METHODS)
def test_two_runs_produce_byte_identical_ttl(tmp_path, method):
    tree = _prepare_tree(tmp_path)
    out1, out2 = tmp_path / "out1.ttl", tmp_path / "out2.ttl"

    run_pipeline(str(tree), [method], out1, workers=1, fmt="turtle", item_id_factory=_deterministic_id_factory())
    run_pipeline(str(tree), [method], out2, workers=1, fmt="turtle", item_id_factory=_deterministic_id_factory())

    assert out1.read_bytes() == out2.read_bytes()


@pytest.mark.parametrize(("method", "recorded_name"), _RECORDED_NAMES)
def test_run_matches_recorded_fixture_byte_for_byte(tmp_path, method, recorded_name):
    tree = _prepare_tree(tmp_path)
    out = tmp_path / "out.ttl"

    run_pipeline(str(tree), [method], out, workers=1, fmt="turtle", item_id_factory=_deterministic_id_factory())

    assert out.read_bytes() == (RECORDED_DIR / recorded_name).read_bytes()


def _write_recorded() -> None:  # pragma: no cover - manual regeneration helper
    """Regenerate the recorded fixtures. Run only on an intentional change; review the diff."""
    import tempfile

    for method, recorded_name in _RECORDED_NAMES:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tree = _prepare_tree(tmp_path)
            out = tmp_path / "out.ttl"
            run_pipeline(str(tree), [method], out, workers=1, fmt="turtle", item_id_factory=_deterministic_id_factory())
            (RECORDED_DIR / recorded_name).write_bytes(out.read_bytes())


if __name__ == "__main__":  # pragma: no cover
    if os.environ.get("CRYSTALIA_REGEN_RECORDED") == "1":
        import unittest.mock

        real_stat = os.stat

        def _pinned(path: object, *a: object, **kw: object) -> _PinnedStat:
            return _PinnedStat(real_stat(path, *a, **kw))  # type: ignore[arg-type]

        with unittest.mock.patch("os.stat", new=_pinned):
            _write_recorded()
