"""Coverage and robustness API (FR-011..013, FR-017; plan 06 Phase 4).

No consumer computes coverage locally. Three own-subject / object-relative / audit
functions plus robustness and comparability, all registry-driven:

* :func:`get_coverage` -- the descriptor's own-subject coverage, dispatched on
  ``TypeEntry.coverage_rule``; never raises (a descriptor's own coverage is always
  well-defined once the descriptor itself is valid).
* :func:`coverage_of` -- coverage relative to a containing object
  (:class:`ObjectContext`), format-aware via a pluggable region-rule table keyed
  by :class:`crystalia_data_model.types.formats.FormatEntry.region_rule`.
* :func:`literal_coverage` -- the audit fallback: bytes hashed over object
  length, or the descriptor's own coverage when it carries no ``length``.
* :func:`get_robustness` -- the registry's robustness for the type, nothing else.
* :func:`asserted` -- the asserted value plus, when a resolver is given, the
  producer's own computed coverage (both are returned when both exist; a
  disagreement is a stale rule or a producer bug, not this function's problem).
* :func:`comparable` -- ETag-subtype comparability rules.

Region rules for :func:`coverage_of` are registered by name via
:func:`register_region_rule`; the format registry only carries the rule's
*name* (``formats.py`` / ``format_rows.py`` are Lane C's). This keeps
``coverage.py`` and ``formats.py`` file-disjoint while letting a verified
format row drive real object-relative coverage once Lane C defines one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from crystalia_data_model.types.canonical import Resolver, mint_composite
from crystalia_data_model.types.errors import DegenerateCoverage
from crystalia_data_model.types.formats import FormatEntry, lookup
from crystalia_data_model.types.registry import CoverageRule, Registry, Robustness, default_registry

if TYPE_CHECKING:
    from collections.abc import Sequence

    from crystalia_data_model.datamodel.linkml_crystalia import Descriptor


@dataclass(frozen=True, slots=True)
class ObjectContext:
    """What :func:`coverage_of` knows about the containing object.

    ``format`` is either a format id (looked up via ``formats.lookup``) or a
    :class:`FormatEntry` supplied directly -- the second form lets tests exercise
    a verified region rule without a Lane C format row.
    """

    length: int | None = None
    format: str | FormatEntry | None = None


RegionRule = Callable[["Descriptor", ObjectContext], float]

_region_rules: dict[str, RegionRule] = {}


def register_region_rule(name: str, rule: RegionRule) -> None:
    """Register the object-relative coverage rule a verified format row names."""
    _region_rules[name] = rule


def _resolve_format(fmt: str | FormatEntry | None) -> FormatEntry | None:
    if fmt is None or isinstance(fmt, FormatEntry):
        return fmt
    return lookup(fmt)


def get_coverage(d: Descriptor, *, registry: Registry | None = None) -> float:
    """The descriptor's own-subject coverage (FR-011); never raises."""
    reg = default_registry() if registry is None else registry
    entry = reg.type_of(d)
    if entry.coverage_rule is CoverageRule.CONSTANT_ONE:
        return 1.0
    if entry.coverage_rule is CoverageRule.PRESENT_OVER_TOTAL:
        total = d.total or 0
        if total <= 0:
            return 0.0
        present = len(d.hasDescriptor or [])
        return present / total
    return d.assertedCoverage if d.assertedCoverage is not None else 0.0


def get_robustness(d: Descriptor, *, registry: Registry | None = None) -> Robustness:
    """Robustness from the registry only (FR-013)."""
    reg = default_registry() if registry is None else registry
    return reg.type_of(d).robustness


def literal_coverage(d: Descriptor, ctx: ObjectContext, *, registry: Registry | None = None) -> float:
    """Bytes hashed over object length, for audit or as the unformatted fallback (FR-012).

    Raises :class:`DegenerateCoverage` when the object length is unknown -- the
    one case :func:`coverage_of` cannot resolve without a format rule.
    """
    if ctx.length is None:
        raise DegenerateCoverage(f"literal coverage of {d.id} needs a known object length")
    if d.length is None:
        return get_coverage(d, registry=registry)
    if ctx.length <= 0:
        return 1.0
    return min(1.0, d.length / ctx.length)


def coverage_of(d: Descriptor, ctx: ObjectContext, *, registry: Registry | None = None) -> float:
    """Coverage relative to the containing object (FR-012; D-5).

    A known format with a *registered* region rule wins; otherwise falls back to
    :func:`literal_coverage`, which raises when the length is also unknown.
    """
    entry = _resolve_format(ctx.format)
    if entry is not None and entry.region_rule is not None:
        rule = _region_rules.get(entry.region_rule)
        if rule is not None:
            return rule(d, ctx)
    return literal_coverage(d, ctx, registry=registry)


def asserted(
    d: Descriptor, *, resolve: Resolver | None = None, registry: Registry | None = None
) -> tuple[float, float | None]:
    """The asserted value and, when resolvable, the producer's own computed coverage (FR-017, AC-17).

    Both are returned when both exist; a disagreement is a stale rule or a
    producer bug, never resolved here.
    """
    asserted_value = d.assertedCoverage if d.assertedCoverage is not None else 0.0
    computed: float | None = None
    if resolve is not None and d.hasDescriptor:
        producer = resolve(str(d.hasDescriptor[0]))
        computed = get_coverage(producer, registry=registry)
    return asserted_value, computed


def mint_md5_chunked(total: int, regions: Sequence[Descriptor], *, registry: Registry | None = None) -> Descriptor:
    """``md5-region`` parts by offset with ``total`` expected (FR-016, AC-08)."""
    return mint_composite("md5-chunked", list(regions), total=total, registry=registry)


def _etag_part_size(d: Descriptor) -> str | None:
    """The part-size tag carried in an ``etag-multipart`` value (convention: ``<etag>#<part-size>``)."""
    value = str(d.value)
    return value.split("#", 1)[1] if "#" in value else None


def comparable(a: Descriptor, b: Descriptor, *, registry: Registry | None = None) -> bool:
    """ETag-subtype comparability (FR-013, AC-18): same subtype, then the subtype's rule."""
    reg = default_registry() if registry is None else registry
    ea, eb = reg.type_of(a), reg.type_of(b)
    if ea.name != eb.name:
        return False
    if ea.name == "etag-multipart":
        return _etag_part_size(a) == _etag_part_size(b)
    if ea.name == "etag-sse":
        return a.id == b.id
    if ea.name == "etag-single":
        return True
    return False


__all__ = [
    "ObjectContext",
    "RegionRule",
    "asserted",
    "comparable",
    "coverage_of",
    "get_coverage",
    "get_robustness",
    "literal_coverage",
    "mint_md5_chunked",
    "register_region_rule",
]
