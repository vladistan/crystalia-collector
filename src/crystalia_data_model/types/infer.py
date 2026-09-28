"""Additive inference framework + the v2 rule set (FR-019, FR-020; steps 6.3-6.4).

Every rule emits its own named, distinct type via :func:`crystalia_data_model.types.canonical.mint_composite`,
so an inferred fact never merges with a harvested one; provenance runs through ``hasDescriptor`` to the
rule's sources. Rules never mutate stored descriptors or Items. Rule inputs are built with
``canonical.mint_*`` directly by the rule's own tests -- this module never imports Lane A/B/C modules
(``leaves.py``, ``coverage.py``, ``bookend.py``, ``formats.py``).

Rules run in a fixed stage order: ``data`` (stored facts only) before ``name-hint`` (weaker, heuristic)
before ``re-probe`` (re-reads the source; skipped, never raised on, when unreachable).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.canonical import Resolver, mint_composite
from crystalia_data_model.types.registry import Registry, default_registry
from crystalia_data_model.types.validate import ensure_valid

Stage = Literal["data", "name-hint", "re-probe"]
_STAGE_ORDER: dict[Stage, int] = {"data": 0, "name-hint": 1, "re-probe": 2}

RuleApply = Callable[[Mapping[str, Descriptor], Resolver, Registry], "Descriptor | None"]


@dataclass(frozen=True, slots=True)
class InferenceRule:
    """One named inference rule: ``in_types`` must all be present (by exact registry type name) for
    ``apply`` to run; a missing input emits nothing. ``reachable`` (re-probe stage only) is checked
    before ``apply``; when it returns ``False`` or raises, the rule is skipped, never raised on.
    """

    name: str
    out_type: str
    in_types: tuple[str, ...]
    apply: RuleApply
    stage: Stage = "data"
    reachable: Callable[[], bool] | None = None


def _small_glimpse_pins_md5(inputs: Mapping[str, Descriptor], resolve: Resolver, registry: Registry) -> Descriptor | None:
    """``glimpse-content`` whose ``file-size`` <= 2 KB pins the whole file: equivalent to ``md5``."""
    glimpse = inputs["glimpse-content"]
    children = [resolve(str(c)) for c in (glimpse.hasDescriptor or [])]
    size = next((c for c in children if registry.is_a(c, "file-size")), None)
    if size is None or size.value is None or int(size.value) > 2048:
        return None
    return mint_composite("md5-from-small-glimpse", [glimpse], registry=registry)


def _md5_equals_region(inputs: Mapping[str, Descriptor], resolve: Resolver, registry: Registry) -> Descriptor | None:
    """Whole-file ``md5`` <-> ``md5-region(0, size)`` equivalence (an inference, never an IRI collapse)."""
    whole, region = inputs["md5"], inputs["md5-region"]
    if region.offset != 0 or region.length != whole.length or region.value != whole.value:
        return None
    return mint_composite("md5-equals-md5-region", [whole, region], registry=registry)


def _bookend_agrees_with_chunks(bookend_type: str) -> RuleApply:
    def _apply(inputs: Mapping[str, Descriptor], resolve: Resolver, registry: Registry) -> Descriptor | None:
        bookend, chunked = inputs[bookend_type], inputs["md5-chunked"]
        regions = [resolve(str(c)) for c in (bookend.hasDescriptor or []) if registry.is_a(resolve(str(c)), "md5-region")]
        head = next((r for r in regions if r.offset == 0), None)
        tail = next((r for r in regions if r is not head), head)
        parts = sorted((resolve(str(c)) for c in (chunked.hasDescriptor or [])), key=lambda d: int(d.offset or 0))
        if head is None or not parts:
            return None
        first, last = parts[0], parts[-1]
        if head.value != first.value or head.length != first.length:
            return None
        if tail is not None and (tail.value != last.value or tail.length != last.length):
            return None
        return mint_composite("bookend-chunked-agreement", [bookend, chunked], registry=registry)

    return _apply


_STRONG_HINT_EXTS: tuple[str, ...] = (".zip", ".xlsx", ".docx", ".jar", ".npz")


def _bookend_strong_by_name(inputs: Mapping[str, Descriptor], resolve: Resolver, registry: Registry) -> Descriptor | None:
    """Name hint only: a strong-family extension on an otherwise weak bookend; never merged with a
    verified ``bookend-strong`` (lower, distinct robustness -- see ``rows/inferred.py``)."""
    bookend, filename = inputs["bookend-weak"], inputs["filename"]
    name = filename.value.lower()
    if not any(name.endswith(ext) for ext in _STRONG_HINT_EXTS):
        return None
    return mint_composite("bookend-strong-by-name", [bookend, filename], registry=registry)


def cross_algorithm_rule(out_type: str, type_a: str, type_b: str, *, stage: Stage = "data") -> InferenceRule:
    """A hash-equivalence rule keyed on (hash, length) between two hash-leaf types: same bytes hashed by
    two algorithms carry the same ``length`` (AC-20 does not apply; this is AC-21's cross-algorithm case).
    No v2 rule uses this directly (md5-only); exercised via a test-registry ``sha256-region`` fixture.
    The output type's robustness is fixed by its registry row to the weakest of the two inputs.
    """

    def _apply(inputs: Mapping[str, Descriptor], resolve: Resolver, registry: Registry) -> Descriptor | None:
        a, b = inputs[type_a], inputs[type_b]
        if a.length != b.length:
            return None
        return mint_composite(out_type, [a, b], registry=registry)

    return InferenceRule(name=out_type, out_type=out_type, in_types=(type_a, type_b), apply=_apply, stage=stage)


DEFAULT_RULES: tuple[InferenceRule, ...] = (
    InferenceRule(
        "md5-from-small-glimpse",
        "md5-from-small-glimpse",
        ("glimpse-content",),
        _small_glimpse_pins_md5,
    ),
    InferenceRule(
        "md5-equals-md5-region",
        "md5-equals-md5-region",
        ("md5", "md5-region"),
        _md5_equals_region,
    ),
    InferenceRule(
        "bookend-chunked-agreement-strong",
        "bookend-chunked-agreement",
        ("bookend-strong", "md5-chunked"),
        _bookend_agrees_with_chunks("bookend-strong"),
    ),
    InferenceRule(
        "bookend-chunked-agreement-weak",
        "bookend-chunked-agreement",
        ("bookend-weak", "md5-chunked"),
        _bookend_agrees_with_chunks("bookend-weak"),
    ),
    InferenceRule(
        "bookend-strong-by-name",
        "bookend-strong-by-name",
        ("bookend-weak", "filename"),
        _bookend_strong_by_name,
        stage="name-hint",
    ),
)


def infer(
    descriptors: Iterable[Descriptor],
    resolve: Resolver,
    *,
    rules: Iterable[InferenceRule] | None = None,
    registry: Registry | None = None,
) -> list[Descriptor]:
    """Run every rule in stage order over ``descriptors`` (grouped by exact registry type name) and
    return the additive set of newly-inferred, already-validated descriptors. ``descriptors`` and
    whatever ``resolve`` reaches are never mutated.
    """
    reg = default_registry() if registry is None else registry
    active = DEFAULT_RULES if rules is None else tuple(rules)
    by_type: dict[str, list[Descriptor]] = {}
    for d in descriptors:
        by_type.setdefault(reg.type_of(d).name, []).append(d)
    out: list[Descriptor] = []
    for rule in sorted(active, key=lambda r: _STAGE_ORDER[r.stage]):
        if rule.stage == "re-probe" and rule.reachable is not None:
            try:
                if not rule.reachable():
                    continue
            except Exception:  # noqa: BLE001 - a probe failure is "unreachable", never a raise (FR-019)
                continue
        inputs: dict[str, Descriptor] = {}
        for type_name in rule.in_types:
            candidates = by_type.get(type_name)
            if not candidates:
                inputs = {}
                break
            inputs[type_name] = candidates[0]
        if not inputs:
            continue
        result = rule.apply(inputs, resolve, reg)
        if result is None:
            continue
        out.append(ensure_valid(result, registry=reg))
    return out


__all__ = ["DEFAULT_RULES", "InferenceRule", "RuleApply", "Stage", "cross_algorithm_rule", "infer"]
