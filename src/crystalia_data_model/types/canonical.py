"""The canonical encoder: the only IRI factory (FR-009, FR-010; SPARC §Canonical Encoding).

Every descriptor IRI is ``cryd:<md5(canonical bytes)>``. The bytes are UTF-8 lines, every value
length-prefixed as ``<field>=<byte-len>:<bytes>``:

* line 1: ``type=`` the type CURIE normalized to ``cryd:desc-type/<name>`` (the type IS the version);
* the type's identity scalars in fixed order ``offset, length, value, total, assertedCoverage``;
* children as bare hex, ordered per kind: fixed-role composites by role order, region composites by
  offset, folder rollups as ``child=<len>:<NFC name> <hex>`` sorted by the NFC UTF-8 bytes of the name,
  asserted / inferred sources by hex.

A composite's stored ``value`` is the same hex as its IRI (asserted types keep the producer's value).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Final, TypeAlias

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.errors import InvalidDescriptor, Violation, ViolationCode
from crystalia_data_model.types.registry import (
    CRYD_BASE,
    CRYD_CURIE_PREFIX,
    Kind,
    Registry,
    TypeEntry,
    default_registry,
    type_curie,
)

Scalar: TypeAlias = int | float | str
Child: TypeAlias = "Descriptor | str"
NamedChild: TypeAlias = tuple[str, "Descriptor | str"]
Resolver: TypeAlias = Callable[[str], Descriptor]

_HEX32: Final = re.compile(r"^[0-9a-f]{32}$")
_NL: Final = b"\n"


# --------------------------------------------------------------------------- primitives


def nfc(name: str) -> str:
    """NFC-normalize a name (macOS NFD spellings collapse onto Linux NFC ones; ruling R10)."""
    return unicodedata.normalize("NFC", name)


def digest(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()  # noqa: S324 - identity digest, not security


def iri_of_hex(hex_value: str) -> str:
    return f"{CRYD_CURIE_PREFIX}{hex_value}"


def hex_of(child: Descriptor | str) -> str:
    """Bare 32-hex from a descriptor or its IRI (CURIE or expanded); rejects anything else."""
    iri = child if isinstance(child, str) else str(child.id)
    if iri.startswith(CRYD_BASE):
        iri = CRYD_CURIE_PREFIX + iri[len(CRYD_BASE) :]
    hex_value = iri[len(CRYD_CURIE_PREFIX) :] if iri.startswith(CRYD_CURIE_PREFIX) else iri
    if not _HEX32.match(hex_value):
        raise InvalidDescriptor(
            [
                Violation(
                    ViolationCode.RANGE,
                    iri,
                    None,
                    "hasDescriptor",
                    f"child {iri!r} is not a cryd:<md5-hex> descriptor IRI",
                )
            ]
        )
    return hex_value


def _scalar_bytes(name: str, value: Scalar) -> bytes:
    if name == "assertedCoverage":
        return repr(float(value)).encode()
    if isinstance(value, bool):  # pragma: no cover - bools never reach here through the typed API
        raise TypeError("bool is not a scalar")
    return str(value).encode()


def _line(key: str, payload: bytes) -> bytes:
    return f"{key}={len(payload)}:".encode() + payload + _NL


def canonical_bytes(
    type_ref: str,
    scalars: Mapping[str, Scalar | None],
    children: Iterable[str | tuple[str, str]] = (),
    *,
    registry: Registry | None = None,
) -> bytes:
    """The published encoding. ``children`` are bare hex (unnamed) or ``(name, hex)`` (named) in final order.

    Only the type's identity scalars are encoded, in registry order; ``None`` values are skipped.
    """
    reg = default_registry() if registry is None else registry
    entry = reg.type_of(type_ref)
    out = bytearray(_line("type", entry.iri.encode()))
    for name in entry.identity_fields:
        value = scalars.get(name)
        if value is not None:
            out += _line(name, _scalar_bytes(name, value))
    for child in children:
        if isinstance(child, tuple):
            name, hex_value = child
            out += _line("child", nfc(name).encode() + b" " + hex_value.encode())
        else:
            out += _line("child", child.encode())
    return bytes(out)


# --------------------------------------------------------------------------- ordering per kind


def _order_by_offset(children: Sequence[Descriptor]) -> list[str]:
    def key(d: Descriptor) -> tuple[int, str]:
        if d.offset is None:
            raise InvalidDescriptor(
                [
                    Violation(
                        ViolationCode.MISSING_REQUIRED, str(d.id), str(d.hasType), "offset", "region part has no offset"
                    )
                ]
            )
        return (int(d.offset), hex_of(d))

    return [hex_of(d) for d in sorted(children, key=key)]


def _order_named(children: Iterable[NamedChild]) -> list[tuple[str, str]]:
    named = [(nfc(name), hex_of(child)) for name, child in children]
    return sorted(named, key=lambda nc: (nc[0].encode(), nc[1]))


def _order_sources(children: Iterable[Descriptor | str]) -> list[str]:
    return sorted(hex_of(c) for c in children)


def _order_roles(entry: TypeEntry, fields: Mapping[str, Descriptor | str], iri: str | None) -> list[str]:
    roles = entry.children.role_names
    missing = [r for r in roles if r not in fields]
    extra = [k for k in fields if k not in roles]
    violations: list[Violation] = []
    if missing:
        violations.append(
            Violation(
                ViolationCode.MISSING_REQUIRED, iri, entry.iri, "hasDescriptor", f"missing role children {missing}"
            )
        )
    if extra:
        violations.append(
            Violation(
                ViolationCode.FORBIDDEN_FIELD,
                iri,
                entry.iri,
                "hasDescriptor",
                f"unknown roles {extra} for {entry.name}",
            )
        )
    if violations:
        raise InvalidDescriptor(violations)
    return [hex_of(fields[r]) for r in roles]


# --------------------------------------------------------------------------- minting


def _build(
    entry: TypeEntry,
    scalars: Mapping[str, Scalar | None],
    ordered: Sequence[str | tuple[str, str]],
    child_iris: Sequence[str],
    *,
    registry: Registry,
) -> Descriptor:
    hex_value = digest(canonical_bytes(entry.name, scalars, ordered, registry=registry))
    given = scalars.get("value")
    value = str(given) if given is not None else hex_value  # a composite's value is its own hex
    violations = registry.contract_violations(entry, {**scalars, "value": value}, len(child_iris), None)
    if violations:
        raise InvalidDescriptor(violations)
    return Descriptor(
        id=iri_of_hex(hex_value),
        hasType=entry.iri,
        value=value,
        offset=scalars.get("offset"),  # type: ignore[arg-type]
        length=scalars.get("length"),  # type: ignore[arg-type]
        total=scalars.get("total"),  # type: ignore[arg-type]
        assertedCoverage=scalars.get("assertedCoverage"),  # type: ignore[arg-type]
        hasDescriptor=list(child_iris) or None,
    )


def _entry_of_kind(type_ref: str, kinds: tuple[Kind, ...], registry: Registry, what: str) -> TypeEntry:
    entry = registry.type_of(type_ref)
    if entry.kind not in kinds or entry.abstract:
        raise InvalidDescriptor(
            [
                Violation(
                    ViolationCode.UNKNOWN_TYPE, None, entry.iri, "hasType", f"{entry.name} is not mintable as {what}"
                )
            ]
        )
    return entry


def mint_leaf(type_ref: str, value: str, *, length: int | None = None, registry: Registry | None = None) -> Descriptor:
    """A fact or hash leaf. Hash leaves take ``length`` = bytes hashed; fact leaves must not."""
    reg = default_registry() if registry is None else registry
    entry = _entry_of_kind(type_ref, (Kind.LEAF,), reg, "a leaf")
    return _build(entry, {"value": value, "length": length}, (), (), registry=reg)


def mint_positional(
    type_ref: str, offset: int, length: int, value: str, *, registry: Registry | None = None
) -> Descriptor:
    """A positional descriptor: the same bytes at another offset are another IRI with the same value."""
    reg = default_registry() if registry is None else registry
    entry = _entry_of_kind(type_ref, (Kind.POSITIONAL,), reg, "positional")
    return _build(entry, {"offset": offset, "length": length, "value": value}, (), (), registry=reg)


def mint_composite(
    type_ref: str,
    children: Mapping[str, Descriptor | str] | Sequence[Descriptor] | Sequence[NamedChild] | Sequence[Descriptor | str],
    *,
    total: int | None = None,
    value: str | None = None,
    asserted_coverage: float | None = None,
    fields: Mapping[str, Descriptor | str] | None = None,
    registry: Registry | None = None,
) -> Descriptor:
    """A composite of the kind the type declares; the child shape follows the kind:

    * field composite: ``children`` is a mapping ``role -> child`` (every role of the type);
    * region composite: ``children`` are the part descriptors (ordered by offset here) and ``total`` is required;
    * rollup: ``children`` are ``(name, child)`` pairs (NFC-sorted here); legacy own-field roles go in ``fields``;
    * asserted: ``children`` is the single producer; ``value`` and ``asserted_coverage`` are required;
    * inferred: ``children`` are the sources (ordered by hex here).
    """
    reg = default_registry() if registry is None else registry
    entry = _entry_of_kind(
        type_ref,
        (Kind.FIELD_COMPOSITE, Kind.REGION_COMPOSITE, Kind.ROLLUP, Kind.ASSERTED, Kind.INFERRED),
        reg,
        "a composite",
    )
    scalars: dict[str, Scalar | None] = {"total": total, "value": value, "assertedCoverage": asserted_coverage}
    ordered: list[str | tuple[str, str]]
    if entry.kind is Kind.FIELD_COMPOSITE:
        if not isinstance(children, Mapping):
            raise TypeError(f"{entry.name}: field composites take a role -> child mapping")
        ordered = list(_order_roles(entry, children, None))
    elif entry.kind is Kind.REGION_COMPOSITE:
        parts = [c for c in children if isinstance(c, Descriptor)]
        if isinstance(children, Mapping) or len(parts) != len(children):
            raise TypeError(f"{entry.name}: region composites take part descriptors")
        ordered = list(_order_by_offset(parts))
    elif entry.kind is Kind.ROLLUP:
        if isinstance(children, Mapping) or any(not isinstance(c, tuple) for c in children):
            raise TypeError(f"{entry.name}: rollups take (name, child) pairs")
        role_hex = _order_roles(entry, fields or {}, None)
        ordered = [*role_hex, *_order_named(children)]  # type: ignore[arg-type]
    else:  # ASSERTED, INFERRED
        if isinstance(children, Mapping):
            raise TypeError(f"{entry.name}: takes source descriptors")
        ordered = list(_order_sources(children))  # type: ignore[arg-type]
    child_iris = [iri_of_hex(c[1] if isinstance(c, tuple) else c) for c in ordered]
    return _build(entry, scalars, ordered, child_iris, registry=reg)


# --------------------------------------------------------------------------- re-identification


def _assign_roles(entry: TypeEntry, children: Sequence[str], resolve: Resolver, registry: Registry) -> list[str]:
    """Reconstruct role order from an unordered child set by resolving each child's type and offset.

    Children of one role type are taken in ``(offset, hex)`` order; a role type with fewer children
    than roles reuses the last one (a file <= 16 KB stores one region IRI for both head and tail,
    which RDF's set semantics collapses to a single edge).
    """
    resolved = {c: resolve(c) for c in children}

    def sort_key(iri: str) -> tuple[int, str]:
        d = resolved[iri]
        return (int(d.offset) if d.offset is not None else -1, hex_of(iri))

    taken: dict[str, int] = {}
    out: list[str] = []
    for role in entry.children.roles:
        cands = sorted((c for c in children if registry.is_a(resolved[c], role.child)), key=sort_key)
        if not cands:
            raise InvalidDescriptor(
                [
                    Violation(
                        ViolationCode.MISSING_REQUIRED,
                        None,
                        entry.iri,
                        "hasDescriptor",
                        f"no child fills role {role.name!r} ({role.child})",
                    )
                ]
            )
        idx = taken.get(role.child, 0)
        out.append(hex_of(cands[min(idx, len(cands) - 1)]))
        taken[role.child] = idx + 1
    return out


def recompute_id(
    d: Descriptor,
    *,
    registry: Registry | None = None,
    resolve: Resolver | None = None,
    child_names: Iterable[NamedChild] | None = None,
) -> str:
    """Re-derive the IRI from a descriptor's stored fields and children.

    In memory a freshly minted descriptor carries its children in canonical order, so no context is
    needed. After an RDF round-trip child order is lost, so pass ``resolve`` (child IRI -> descriptor)
    to rebuild role and offset order, and for folder rollups pass ``child_names`` (the ``(name, child)``
    entries, which the stored model does not carry).
    """
    reg = default_registry() if registry is None else registry
    entry = reg.type_of(d)
    scalars: dict[str, Scalar | None] = {
        "offset": d.offset,
        "length": d.length,
        "value": d.value,
        "total": d.total,
        "assertedCoverage": d.assertedCoverage,
    }
    stored = [str(c) for c in (d.hasDescriptor or [])]
    ordered: list[str | tuple[str, str]]
    if entry.kind in (Kind.LEAF, Kind.POSITIONAL):
        ordered = []
    elif entry.kind is Kind.FIELD_COMPOSITE:
        ordered = (
            list(_assign_roles(entry, stored, resolve, reg)) if resolve is not None else [hex_of(c) for c in stored]
        )
    elif entry.kind is Kind.REGION_COMPOSITE:
        ordered = (
            list(_order_by_offset([resolve(c) for c in stored])) if resolve is not None else [hex_of(c) for c in stored]
        )
    elif entry.kind is Kind.ROLLUP:
        if child_names is None:
            raise TypeError(
                f"{entry.name}: recompute_id of a folder rollup needs child_names (the stored model carries no entry names)"
            )
        named = _order_named(child_names)
        named_set = {h for _, h in named}
        role_children = [c for c in stored if hex_of(c) not in named_set]
        roles = (
            list(_assign_roles(entry, role_children, resolve, reg))
            if resolve is not None
            else [hex_of(c) for c in role_children]
        )
        ordered = [*roles, *named]
    else:  # ASSERTED, INFERRED
        ordered = list(_order_sources(stored))
    return iri_of_hex(digest(canonical_bytes(entry.name, scalars, ordered, registry=reg)))


__all__ = [
    "Resolver",
    "canonical_bytes",
    "digest",
    "hex_of",
    "iri_of_hex",
    "mint_composite",
    "mint_leaf",
    "mint_positional",
    "nfc",
    "recompute_id",
    "type_curie",
]
