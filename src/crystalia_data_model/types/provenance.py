"""Content-addressed provenance: ``Method`` and ``HarvestRecord`` construction (FR-006, FR-007; step 6.1-6.2).

``Method`` is content-addressed by (name, canonical parameter set) so one node is reused across every
harvest that uses the same method with the same parameters. ``HarvestRecord`` gets a fresh, unique IRI
per harvest run and links the methods it used and the root ``Item``s it produced. Neither of these is a
``Descriptor``, so they are minted here rather than through :mod:`crystalia_data_model.types.canonical`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from datetime import datetime
from uuid import uuid4

from crystalia_data_model.datamodel.linkml_crystalia import HarvestRecord, Item, Method
from crystalia_data_model.types.registry import CRYD_CURIE_PREFIX

_METHOD_NAMESPACE = "method/"
_HARVEST_NAMESPACE = "harvest/"


def _digest(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()  # noqa: S324 - identity digest, not security


def _line(key: str, value: str) -> str:
    return f"{key}={len(value.encode())}:{value}"


def canonical_parameters(parameters: Mapping[str, str] | None) -> str:
    """The canonical parameter string: sorted, length-prefixed ``key=len:value`` lines (SPARC §6.1)."""
    lines = sorted(_line(key, value) for key, value in (parameters or {}).items())
    return "\n".join(lines)


def mint_method(name: str, parameters: Mapping[str, str] | None = None, *, comment: str | None = None) -> Method:
    """One ``Method`` node per (name, parameters); param order and dict identity are irrelevant (AC-20)."""
    params = canonical_parameters(parameters)
    payload = (_line("name", name) + "\n" + _line("parameters", params)).encode()
    method_id = f"{CRYD_CURIE_PREFIX}{_METHOD_NAMESPACE}{_digest(payload)}"
    return Method(id=method_id, label=name, comment=comment, parameters=params or None)


def record_harvest(
    started: datetime | None,
    ended: datetime | None,
    collector_version: str | None,
    source_root: str | None,
    methods: Iterable[Method] = (),
    roots: Iterable[Item] = (),
) -> HarvestRecord:
    """A new, uniquely-IRI'd ``HarvestRecord`` linking the methods used and the root items produced (AC-20)."""
    harvest_id = f"{CRYD_CURIE_PREFIX}{_HARVEST_NAMESPACE}{uuid4()}"
    uses_method = [str(m.id) for m in methods]
    has_root = [str(r.id) for r in roots]
    return HarvestRecord(
        id=harvest_id,
        startedAt=started,
        endedAt=ended,
        collectorVersion=collector_version,
        sourceRoot=source_root,
        usesMethod=uses_method or None,
        hasRoot=has_root or None,
    )


__all__ = ["canonical_parameters", "mint_method", "record_harvest"]
