"""Lane A behaviour: pure, name-aware folder rollups (FR-017, AC-04, AC-13, AC-15).

``rollup_dir`` builds a folder rollup from ``(name, child)`` pairs only; it never touches a
filesystem or a store. It is pure (mergeable over per-job outputs, ruling C1/AC-15) and raises
``IncompleteRollup`` rather than mint an incomplete folder — there are no ``-incomplete`` types.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.canonical import NamedChild, mint_composite
from crystalia_data_model.types.errors import IncompleteRollup, InvalidDescriptor, Violation, ViolationCode
from crystalia_data_model.types.registry import Registry


def rollup_dir(
    type_family: str,
    expected: int,
    children: Iterable[NamedChild],
    *,
    fields: Mapping[str, Descriptor | str] | None = None,
    registry: Registry | None = None,
) -> Descriptor:
    """Mint a folder rollup of ``type_family`` over its named children.

    ``expected`` is the entry count from the harvest's own listing, never stored (folder rollups
    carry no ``total``). Fewer children than ``expected`` means an entry is missing by failure and
    raises :class:`IncompleteRollup`; more than ``expected`` is a broken contract. Pure over
    ``children``, so a rollup built from per-job outputs equals one built in a single pass (AC-15).
    """
    named = list(children)
    present = len(named)
    if present < expected:
        raise IncompleteRollup(expected, present)
    if present > expected:
        raise InvalidDescriptor(
            [
                Violation(
                    ViolationCode.RANGE,
                    None,
                    None,
                    "hasDescriptor",
                    f"{type_family}: {present} children exceeds expected {expected}",
                )
            ]
        )
    return mint_composite(type_family, named, fields=fields, registry=registry)


def mint_glimpse_dir_content(
    expected: int, children: Iterable[NamedChild], *, registry: Registry | None = None
) -> Descriptor:
    """Mtime-free folder rollup over ``glimpse-content`` children (AC-09)."""
    return rollup_dir("glimpse-dir-content", expected, children, registry=registry)


def mint_glimpse_dir(
    expected: int,
    children: Iterable[NamedChild],
    *,
    filename: Descriptor | str,
    mtime: Descriptor | str,
    count: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    """Legacy v1 directory glimpse: own filename/mtime/count then the named rollup."""
    return rollup_dir(
        "glimpse-dir",
        expected,
        children,
        fields={"filename": filename, "mtime": mtime, "count": count},
        registry=registry,
    )


def mint_glimpse_dir_slim(
    expected: int,
    children: Iterable[NamedChild],
    *,
    filename: Descriptor | str,
    mtime: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return rollup_dir(
        "glimpse-dir-slim", expected, children, fields={"filename": filename, "mtime": mtime}, registry=registry
    )


def mint_glimpse_dir_light(
    expected: int,
    children: Iterable[NamedChild],
    *,
    mtime: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return rollup_dir("glimpse-dir-light", expected, children, fields={"mtime": mtime}, registry=registry)


__all__ = [
    "mint_glimpse_dir",
    "mint_glimpse_dir_content",
    "mint_glimpse_dir_light",
    "mint_glimpse_dir_slim",
    "rollup_dir",
]
