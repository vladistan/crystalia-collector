"""Generic, registry-driven descriptor validation (FR-018; plan 06 step 2.5).

Checks, in order: the type is known (else nothing else is checked), required / forbidden scalars,
ranges, child-count bounds, present <= total on region composites, a composite's ``value`` equals
its IRI hex, and ``id == recompute_id`` (``IRI_MISMATCH``). No per-type code.
"""

from __future__ import annotations

from collections.abc import Iterable

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.canonical import NamedChild, Resolver, hex_of, recompute_id
from crystalia_data_model.types.errors import InvalidDescriptor, UnknownType, Violation, ViolationCode
from crystalia_data_model.types.registry import Kind, Registry, default_registry


def validate(
    d: Descriptor,
    *,
    registry: Registry | None = None,
    resolve: Resolver | None = None,
    child_names: Iterable[NamedChild] | None = None,
) -> list[Violation]:
    """Every violation of the descriptor's type contract; empty when valid.

    ``resolve`` and ``child_names`` feed :func:`recompute_id` after an RDF load (child order is not
    stored; rollup entry names are not stored). Without ``child_names`` a folder rollup's IRI cannot
    be re-derived, so that one check is skipped for rollups — every other check still runs.
    """
    reg = default_registry() if registry is None else registry
    iri = str(d.id)
    try:
        entry = reg.type_of(d)
    except UnknownType as exc:
        return [Violation(ViolationCode.UNKNOWN_TYPE, iri, str(d.hasType), "hasType", str(exc))]
    scalars = {
        "offset": d.offset,
        "length": d.length,
        "value": d.value,
        "total": d.total,
        "assertedCoverage": d.assertedCoverage,
    }
    children = [str(c) for c in (d.hasDescriptor or [])]
    out = reg.contract_violations(entry, scalars, len(children), iri)
    if entry.abstract:
        return out
    try:
        own_hex = hex_of(iri)
        for c in children:
            hex_of(c)
    except InvalidDescriptor as exc:
        return [*out, *exc.violations]
    if entry.kind not in (Kind.LEAF, Kind.POSITIONAL, Kind.ASSERTED) and d.value != own_hex:
        out.append(
            Violation(ViolationCode.IRI_MISMATCH, iri, entry.iri, "value", "composite value must equal the IRI hex")
        )
    if entry.kind is Kind.ROLLUP and child_names is None:
        return out
    if any(
        v.code in (ViolationCode.MISSING_REQUIRED, ViolationCode.FORBIDDEN_FIELD) and v.field == "hasDescriptor"
        for v in out
    ):
        return out
    try:
        expected = recompute_id(d, registry=reg, resolve=resolve, child_names=child_names)
    except InvalidDescriptor as exc:
        return [*out, *exc.violations]
    if expected != iri:
        out.append(
            Violation(ViolationCode.IRI_MISMATCH, iri, entry.iri, "id", f"stored id differs from recomputed {expected}")
        )
    return out


def ensure_valid(
    d: Descriptor,
    *,
    registry: Registry | None = None,
    resolve: Resolver | None = None,
    child_names: Iterable[NamedChild] | None = None,
) -> Descriptor:
    """Return ``d`` unchanged, or raise :class:`InvalidDescriptor` with every violation found."""
    violations = validate(d, registry=registry, resolve=resolve, child_names=child_names)
    if violations:
        raise InvalidDescriptor(violations)
    return d


__all__ = ["ensure_valid", "validate"]
