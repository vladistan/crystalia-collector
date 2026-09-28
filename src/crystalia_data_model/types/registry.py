"""Type registry: the hierarchy and per-type semantics keyed by ``hasType`` (FR-008).

The stored model knows only ``Descriptor.hasType``; everything a type *means*
(kind, grade, robustness, strength, coverage rule, which fields it requires or
forbids, how its children are ordered) lives here, in frozen rows. Rows are
authored per owning lane under :mod:`crystalia_data_model.types.rows`; this
module owns the shapes, the row constructors, the structural (abstract) rows
and the lookup API.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from functools import cache
from typing import TYPE_CHECKING, Literal

from crystalia_data_model.types.errors import RegistryLoadError, UnknownType, Violation, ViolationCode

if TYPE_CHECKING:
    from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

CRYD_CURIE_PREFIX = "cryd:"
CRYD_BASE = "https://crystalia.link/data/"
TYPE_NAMESPACE = "desc-type/"

#: Scalar slots that can carry identity, in canonical encoding order (SPARC §Canonical Encoding).
SCALARS: tuple[str, ...] = ("offset", "length", "value", "total", "assertedCoverage")


class Kind(StrEnum):
    LEAF = "leaf"
    POSITIONAL = "positional"
    FIELD_COMPOSITE = "field_composite"
    REGION_COMPOSITE = "region_composite"
    ROLLUP = "rollup"
    ASSERTED = "asserted"
    INFERRED = "inferred"


class Grade(StrEnum):
    COMPARISON = "comparison"
    AUTHORITY = "authority"
    LOCATION = "location"


class Robustness(IntEnum):
    """Ordered: ``EXTREMELY_HIGH > VERY_HIGH > HIGH > MODERATE > LOW > VERY_LOW``."""

    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5
    EXTREMELY_HIGH = 6


class CoverageRule(StrEnum):
    CONSTANT_ONE = "constant_one"
    PRESENT_OVER_TOTAL = "present_over_total"
    ASSERTED = "asserted"


Order = Literal["none", "roles", "offset", "named", "sources"]


@dataclass(frozen=True, slots=True)
class Role:
    """A fixed-role child slot of a field composite: ``name`` filled by a child of type ``child`` (or a subtype)."""

    name: str
    child: str


@dataclass(frozen=True, slots=True)
class ChildrenSpec:
    """How a type's ``hasDescriptor`` children are counted and ordered in its identity.

    ``roles``   fixed-role children, in encoding order (field composites; legacy rollups' own fields)
    ``order``   how the *remaining* children are ordered: ``offset`` (region), ``named`` (rollup),
                ``sources`` (asserted / inferred, by hex), ``none`` (no further children allowed)
    ``min_extra`` / ``max_extra``  bounds on the number of non-role children (``None`` = unbounded)
    """

    roles: tuple[Role, ...] = ()
    order: Order = "none"
    min_extra: int = 0
    max_extra: int | None = 0

    @property
    def role_names(self) -> tuple[str, ...]:
        return tuple(r.name for r in self.roles)


@dataclass(frozen=True, slots=True)
class TypeEntry:
    """One row of the type table. Frozen; the name is the contract (version by name)."""

    name: str
    parent: str | None
    kind: Kind
    grade: Grade
    robustness: Robustness
    strong: bool
    coverage_rule: CoverageRule
    required: frozenset[str]
    forbidden: frozenset[str]
    identity_fields: tuple[str, ...]
    children: ChildrenSpec = field(default_factory=ChildrenSpec)
    derived_from: tuple[str, ...] = ()
    doc: str = ""
    abstract: bool = False

    @property
    def iri(self) -> str:
        return f"{CRYD_CURIE_PREFIX}{TYPE_NAMESPACE}{self.name}"

    @property
    def fields(self) -> tuple[str, ...]:
        """Scalars this type may store, in canonical order."""
        return tuple(s for s in SCALARS if s not in self.forbidden)


def type_name(ref: str) -> str:
    """Bare type name from a name, a ``cryd:desc-type/<name>`` CURIE or the expanded URI."""
    if ref.startswith(CRYD_BASE):
        ref = CRYD_CURIE_PREFIX + ref[len(CRYD_BASE) :]
    if ref.startswith(CRYD_CURIE_PREFIX):
        ref = ref[len(CRYD_CURIE_PREFIX) :]
    if ref.startswith(TYPE_NAMESPACE):
        ref = ref[len(TYPE_NAMESPACE) :]
    return ref


def type_curie(ref: str) -> str:
    return f"{CRYD_CURIE_PREFIX}{TYPE_NAMESPACE}{type_name(ref)}"


# --------------------------------------------------------------------------- row constructors

_ALL = frozenset(SCALARS)
_NOT_ASSERTED = frozenset({"assertedCoverage"})


def _row(
    name: str,
    parent: str | None,
    kind: Kind,
    *,
    grade: Grade,
    robustness: Robustness,
    strong: bool,
    coverage_rule: CoverageRule,
    required: Iterable[str],
    identity_fields: Iterable[str],
    children: ChildrenSpec | None = None,
    optional: Iterable[str] = (),
    derived_from: Iterable[str] = (),
    doc: str = "",
    abstract: bool = False,
) -> TypeEntry:
    req = frozenset(required)
    allowed = req | frozenset(optional)
    return TypeEntry(
        name=name,
        parent=parent,
        kind=kind,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=coverage_rule,
        required=req,
        forbidden=_ALL - allowed,
        identity_fields=tuple(s for s in SCALARS if s in set(identity_fields)),
        children=children or ChildrenSpec(),
        derived_from=tuple(derived_from),
        doc=doc,
        abstract=abstract,
    )


def abstract_row(name: str, parent: str | None, kind: Kind, doc: str = "") -> TypeEntry:
    """A structural node of the hierarchy; never minted or stored."""
    return _row(
        name,
        parent,
        kind,
        grade=Grade.COMPARISON,
        robustness=Robustness.VERY_LOW,
        strong=False,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value",),
        identity_fields=("value",),
        doc=doc,
        abstract=True,
    )


def fact_leaf(name: str, grade: Grade, *, robustness: Robustness = Robustness.VERY_LOW, doc: str = "") -> TypeEntry:
    """A plain fact about the object (filename, size, mtime, ...): identity = (type, value)."""
    return _row(
        name,
        "fact",
        Kind.LEAF,
        grade=grade,
        robustness=robustness,
        strong=False,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value",),
        identity_fields=("value",),
        doc=doc,
    )


def hash_leaf(name: str, grade: Grade, robustness: Robustness, *, strong: bool = True, doc: str = "") -> TypeEntry:
    """A digest over bytes: identity = (type, length = bytes hashed, value)."""
    return _row(
        name,
        "hash",
        Kind.LEAF,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value", "length"),
        identity_fields=("length", "value"),
        doc=doc,
    )


def plain_leaf(
    name: str, grade: Grade, robustness: Robustness, *, strong: bool = False, parent: str = "leaf", doc: str = ""
) -> TypeEntry:
    """A leaf whose identity is (type, value) only and which carries no length (e.g. zip-manifest, ETags)."""
    return _row(
        name,
        parent,
        Kind.LEAF,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value",),
        identity_fields=("value",),
        doc=doc,
    )


def positional(name: str, grade: Grade, robustness: Robustness, *, strong: bool = True, doc: str = "") -> TypeEntry:
    """A digest over a byte range: identity = (type, offset, length, value)."""
    return _row(
        name,
        "positional",
        Kind.POSITIONAL,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("offset", "length", "value"),
        identity_fields=("offset", "length", "value"),
        doc=doc,
    )


def field_composite(
    name: str,
    roles: Iterable[tuple[str, str]],
    grade: Grade,
    robustness: Robustness,
    *,
    strong: bool = False,
    parent: str = "field",
    doc: str = "",
) -> TypeEntry:
    """A composite over fixed-role children; identity = (type, children by role order)."""
    spec = ChildrenSpec(roles=tuple(Role(n, c) for n, c in roles), order="none", min_extra=0, max_extra=0)
    return _row(
        name,
        parent,
        Kind.FIELD_COMPOSITE,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value",),
        identity_fields=(),
        children=spec,
        doc=doc,
    )


def region_composite(name: str, grade: Grade, robustness: Robustness, *, part: str, doc: str = "") -> TypeEntry:
    """A composite over positional parts with a ``total`` expected; strong only when present == total."""
    spec = ChildrenSpec(roles=(), order="offset", min_extra=0, max_extra=None)
    return _row(
        name,
        "region",
        Kind.REGION_COMPOSITE,
        grade=grade,
        robustness=robustness,
        strong=True,
        coverage_rule=CoverageRule.PRESENT_OVER_TOTAL,
        required=("value", "total"),
        identity_fields=("total",),
        children=spec,
        derived_from=(part,),
        doc=doc,
    )


def rollup(
    name: str,
    grade: Grade,
    robustness: Robustness,
    *,
    strong: bool = False,
    roles: Iterable[tuple[str, str]] = (),
    doc: str = "",
) -> TypeEntry:
    """A name-aware folder rollup (git-tree style); complete by construction, no ``total``.

    ``roles`` are the legacy own-field children (``glimpse-dir``'s filename/mtime/count) that precede
    the named entries in the encoding; v2 content rollups have none.
    """
    spec = ChildrenSpec(roles=tuple(Role(n, c) for n, c in roles), order="named", min_extra=0, max_extra=None)
    return _row(
        name,
        "rollup",
        Kind.ROLLUP,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value",),
        identity_fields=(),
        children=spec,
        doc=doc,
    )


def asserted_type(name: str = "asserted", doc: str = "") -> TypeEntry:
    """Coverage asserted by an opaque producer: identity = (type, value, assertedCoverage, producer child)."""
    spec = ChildrenSpec(roles=(), order="sources", min_extra=1, max_extra=1)
    return _row(
        name,
        "descriptor",
        Kind.ASSERTED,
        grade=Grade.COMPARISON,
        robustness=Robustness.VERY_LOW,
        strong=False,
        coverage_rule=CoverageRule.ASSERTED,
        required=("value", "assertedCoverage"),
        identity_fields=("value", "assertedCoverage"),
        children=spec,
        doc=doc,
    )


def inferred(
    name: str, derived_from: Iterable[str], grade: Grade, robustness: Robustness, *, strong: bool = False, doc: str = ""
) -> TypeEntry:
    """An inferred equivalence: identity = (type, source children by hex); provenance via ``hasDescriptor``."""
    spec = ChildrenSpec(roles=(), order="sources", min_extra=1, max_extra=None)
    return _row(
        name,
        "inferred",
        Kind.INFERRED,
        grade=grade,
        robustness=robustness,
        strong=strong,
        coverage_rule=CoverageRule.CONSTANT_ONE,
        required=("value",),
        identity_fields=(),
        children=spec,
        derived_from=derived_from,
        doc=doc,
    )


#: The hierarchy's structural nodes (SPARC §Type hierarchy). Concrete rows hang off these.
STRUCTURAL_ROWS: tuple[TypeEntry, ...] = (
    abstract_row("descriptor", None, Kind.LEAF, "root of the hierarchy"),
    abstract_row("leaf", "descriptor", Kind.LEAF, "single-valued descriptors"),
    abstract_row("fact", "leaf", Kind.LEAF, "plain facts about the object"),
    abstract_row("hash", "leaf", Kind.LEAF, "digests over bytes; carry length = bytes hashed"),
    abstract_row("positional", "descriptor", Kind.POSITIONAL, "digests over a byte range"),
    abstract_row("composite", "descriptor", Kind.FIELD_COMPOSITE, "descriptors over child descriptors"),
    abstract_row("field", "composite", Kind.FIELD_COMPOSITE, "fixed-role composites"),
    abstract_row("region", "composite", Kind.REGION_COMPOSITE, "composites over positional parts with a total"),
    abstract_row("rollup", "composite", Kind.ROLLUP, "name-aware folder rollups"),
    abstract_row("inferred", "descriptor", Kind.INFERRED, "outputs of inference rules"),
)


# --------------------------------------------------------------------------- registry


class Registry:
    """An immutable lookup over a validated set of rows."""

    def __init__(self, rows: Iterable[TypeEntry]) -> None:
        by_name: dict[str, TypeEntry] = {}
        for row in rows:
            if not isinstance(row, TypeEntry):
                raise RegistryLoadError(f"row is not a TypeEntry: {row!r}")
            if row.name in by_name:
                raise RegistryLoadError(f"duplicate type row: {row.name!r}")
            by_name[row.name] = row
        for row in by_name.values():
            self._check_row(row, by_name)
        self._by_name: Mapping[str, TypeEntry] = by_name

    @staticmethod
    def _check_row(row: TypeEntry, by_name: Mapping[str, TypeEntry]) -> None:
        if not row.name or type_name(row.name) != row.name or "/" in row.name:
            raise RegistryLoadError(f"bad type name: {row.name!r}")
        if row.parent is not None and row.parent not in by_name:
            raise RegistryLoadError(f"{row.name}: unknown parent {row.parent!r}")
        if row.parent is None and row.name != "descriptor":
            raise RegistryLoadError(f"{row.name}: only 'descriptor' may be a root")
        seen = {row.name}
        cur = row.parent
        while cur is not None:
            if cur in seen:
                raise RegistryLoadError(f"{row.name}: cycle through {cur!r}")
            seen.add(cur)
            cur = by_name[cur].parent
        if not row.required <= _ALL or not row.forbidden <= _ALL:
            raise RegistryLoadError(f"{row.name}: required/forbidden must be drawn from {SCALARS}")
        if row.required & row.forbidden:
            raise RegistryLoadError(f"{row.name}: a field is both required and forbidden")
        if "value" not in row.required:
            raise RegistryLoadError(f"{row.name}: 'value' is required on every type")
        if set(row.identity_fields) & row.forbidden:
            raise RegistryLoadError(f"{row.name}: identity field is forbidden")
        if row.name.endswith("-incomplete"):
            raise RegistryLoadError(f"{row.name}: no incomplete types exist (ruling C1)")
        if row.abstract:
            return
        if row.kind is Kind.REGION_COMPOSITE and row.coverage_rule is not CoverageRule.PRESENT_OVER_TOTAL:
            raise RegistryLoadError(f"{row.name}: region composites use PRESENT_OVER_TOTAL")
        if row.kind is not Kind.REGION_COMPOSITE and "total" not in row.forbidden:
            raise RegistryLoadError(f"{row.name}: only region composites carry total (ruling C1)")
        if row.kind is Kind.ASSERTED and row.coverage_rule is not CoverageRule.ASSERTED:
            raise RegistryLoadError(f"{row.name}: asserted types use the ASSERTED rule")
        if row.kind is not Kind.ASSERTED and "assertedCoverage" not in row.forbidden:
            raise RegistryLoadError(f"{row.name}: only asserted types carry assertedCoverage")
        if row.kind is not Kind.POSITIONAL and "offset" not in row.forbidden:
            raise RegistryLoadError(f"{row.name}: only positional types carry offset (FR-003)")
        for role in row.children.roles:
            if role.child not in by_name:
                raise RegistryLoadError(f"{row.name}: role {role.name!r} names unknown type {role.child!r}")
        names = row.children.role_names
        if len(set(names)) != len(names):
            raise RegistryLoadError(f"{row.name}: duplicate role names")
        for src in row.derived_from:
            if src not in by_name:
                raise RegistryLoadError(f"{row.name}: derived_from names unknown type {src!r}")

    # ---- lookup

    def __contains__(self, ref: object) -> bool:
        return isinstance(ref, str) and type_name(ref) in self._by_name

    def __iter__(self) -> Iterator[TypeEntry]:
        return iter(self._by_name.values())

    def __len__(self) -> int:
        return len(self._by_name)

    def names(self) -> tuple[str, ...]:
        return tuple(self._by_name)

    def concrete(self) -> tuple[TypeEntry, ...]:
        return tuple(e for e in self._by_name.values() if not e.abstract)

    def type_of(self, ref: str | Descriptor) -> TypeEntry:
        """The row for a type reference or a descriptor's ``hasType``; raises :class:`UnknownType`."""
        key = ref if isinstance(ref, str) else str(ref.hasType)
        entry = self._by_name.get(type_name(key))
        if entry is None:
            raise UnknownType(key)
        return entry

    def ancestors(self, ref: str | Descriptor) -> tuple[TypeEntry, ...]:
        """Proper ancestors, nearest first, root (``descriptor``) last."""
        out: list[TypeEntry] = []
        cur = self.type_of(ref).parent
        while cur is not None:
            entry = self._by_name[cur]
            out.append(entry)
            cur = entry.parent
        return tuple(out)

    def is_a(self, ref: str | Descriptor, ancestor: str) -> bool:
        """True if ``ref`` is ``ancestor`` or descends from it. Unknown ``ancestor`` → False."""
        target = type_name(ancestor)
        entry = self.type_of(ref)
        if entry.name == target:
            return True
        return any(a.name == target for a in self.ancestors(ref))

    def grade(self, ref: str | Descriptor) -> Grade:
        return self.type_of(ref).grade

    def robustness(self, ref: str | Descriptor) -> Robustness:
        return self.type_of(ref).robustness

    def is_strong(self, d: Descriptor) -> bool:
        """The type's strong flag AND, for region composites, every expected part present."""
        entry = self.type_of(d)
        if not entry.strong:
            return False
        if entry.kind is Kind.REGION_COMPOSITE:
            present = len(d.hasDescriptor or [])
            return d.total is not None and present == d.total
        return True

    def extend(self, rows: Iterable[TypeEntry]) -> Registry:
        """A new registry with extra rows (test overlays); this one is unchanged."""
        return Registry((*self._by_name.values(), *rows))

    # ---- contract checks shared by minting and validation

    def contract_violations(
        self,
        entry: TypeEntry,
        scalars: Mapping[str, int | float | str | None],
        n_children: int,
        iri: str | None,
    ) -> list[Violation]:
        """Required/forbidden scalars, ranges and child-count bounds for ``entry``; no IRI check."""
        out: list[Violation] = []
        t = entry.iri
        if entry.abstract:
            out.append(Violation(ViolationCode.UNKNOWN_TYPE, iri, t, "hasType", f"{entry.name!r} is abstract"))
        for name in SCALARS:
            val = scalars.get(name)
            if name in entry.required and val is None:
                out.append(Violation(ViolationCode.MISSING_REQUIRED, iri, t, name, f"{entry.name} requires {name}"))
            elif name in entry.forbidden and val is not None:
                out.append(Violation(ViolationCode.FORBIDDEN_FIELD, iri, t, name, f"{entry.name} forbids {name}"))
        offset, length, total, cov = (
            scalars.get("offset"),
            scalars.get("length"),
            scalars.get("total"),
            scalars.get("assertedCoverage"),
        )
        if isinstance(offset, int) and offset < 0:
            out.append(Violation(ViolationCode.RANGE, iri, t, "offset", "offset must be >= 0"))
        if isinstance(length, int) and length < 0:
            out.append(Violation(ViolationCode.RANGE, iri, t, "length", "length must be >= 0"))
        if isinstance(total, int) and total < 1:
            out.append(Violation(ViolationCode.RANGE, iri, t, "total", "total must be >= 1"))
        if isinstance(cov, (int, float)) and not 0.0 <= float(cov) <= 1.0:
            out.append(
                Violation(ViolationCode.RANGE, iri, t, "assertedCoverage", "assertedCoverage must be within [0, 1]")
            )
        spec = entry.children
        n_roles = len(spec.roles)
        # Roles of one child type may share a child (a file <= 16 KB stores one md5-region for head
        # and tail; RDF keeps a single edge), so the floor is the number of distinct role child types.
        min_roles = len({r.child for r in spec.roles})
        extra = max(0, n_children - n_roles)
        if n_children < min_roles:
            out.append(
                Violation(
                    ViolationCode.MISSING_REQUIRED,
                    iri,
                    t,
                    "hasDescriptor",
                    f"{entry.name} needs {min_roles}..{n_roles} role children, got {n_children}",
                )
            )
        elif extra < spec.min_extra:
            out.append(
                Violation(
                    ViolationCode.MISSING_REQUIRED,
                    iri,
                    t,
                    "hasDescriptor",
                    f"{entry.name} needs at least {spec.min_extra} children beyond its roles",
                )
            )
        elif spec.max_extra is not None and extra > spec.max_extra:
            code = ViolationCode.FORBIDDEN_FIELD if spec.max_extra == 0 and n_roles == 0 else ViolationCode.RANGE
            out.append(
                Violation(
                    code,
                    iri,
                    t,
                    "hasDescriptor",
                    f"{entry.name} allows at most {n_roles + spec.max_extra} children, got {n_children}",
                )
            )
        if entry.kind is Kind.REGION_COMPOSITE and isinstance(total, int) and total >= 1 and n_children > total:
            out.append(
                Violation(ViolationCode.RANGE, iri, t, "total", f"present ({n_children}) exceeds total ({total})")
            )
        return out


@cache
def default_registry() -> Registry:
    """The v2 type table: structural rows plus every lane's rows."""
    from crystalia_data_model.types import rows

    return Registry((*STRUCTURAL_ROWS, *rows.ROWS))


def _reg(registry: Registry | None) -> Registry:
    return default_registry() if registry is None else registry


def type_of(ref: str | Descriptor, *, registry: Registry | None = None) -> TypeEntry:
    return _reg(registry).type_of(ref)


def ancestors(ref: str | Descriptor, *, registry: Registry | None = None) -> tuple[TypeEntry, ...]:
    return _reg(registry).ancestors(ref)


def is_a(ref: str | Descriptor, ancestor: str, *, registry: Registry | None = None) -> bool:
    return _reg(registry).is_a(ref, ancestor)


def grade(ref: str | Descriptor, *, registry: Registry | None = None) -> Grade:
    return _reg(registry).grade(ref)


def is_strong(d: Descriptor, *, registry: Registry | None = None) -> bool:
    return _reg(registry).is_strong(d)


__all__ = [
    "CRYD_BASE",
    "CRYD_CURIE_PREFIX",
    "SCALARS",
    "STRUCTURAL_ROWS",
    "TYPE_NAMESPACE",
    "ChildrenSpec",
    "CoverageRule",
    "Grade",
    "Kind",
    "Registry",
    "Robustness",
    "Role",
    "TypeEntry",
    "abstract_row",
    "ancestors",
    "asserted_type",
    "default_registry",
    "fact_leaf",
    "field_composite",
    "grade",
    "hash_leaf",
    "inferred",
    "is_a",
    "is_strong",
    "plain_leaf",
    "positional",
    "region_composite",
    "rollup",
    "type_curie",
    "type_name",
    "type_of",
]
