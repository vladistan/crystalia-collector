"""Error taxonomy and the :class:`Violation` record (SPARC §Refinement, plan 06 step 2.1).

Principle: malformed *data* is never raised on (it degrades to WEAK / OPAQUE);
a broken *contract* or a missing-by-failure entry raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ViolationCode(StrEnum):
    """Stable codes consumers aggregate by (NFR-007)."""

    UNKNOWN_TYPE = "UNKNOWN_TYPE"
    MISSING_REQUIRED = "MISSING_REQUIRED"
    FORBIDDEN_FIELD = "FORBIDDEN_FIELD"
    RANGE = "RANGE"
    IRI_MISMATCH = "IRI_MISMATCH"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True, slots=True)
class Violation:
    """One contract violation found by :func:`crystalia_data_model.types.validate.validate`."""

    code: ViolationCode
    iri: str | None
    type: str | None
    field: str | None
    detail: str

    def __str__(self) -> str:
        where = f" {self.field}" if self.field else ""
        return f"{self.code}{where}: {self.detail} (iri={self.iri}, type={self.type})"


class CrystaliaModelError(Exception):
    """Base of every error raised by the behaviour package."""


class UnknownType(CrystaliaModelError):
    """``hasType`` is not in the type registry."""

    def __init__(self, type_iri: str) -> None:
        super().__init__(f"unknown descriptor type: {type_iri!r}")
        self.type_iri = type_iri


class InvalidDescriptor(CrystaliaModelError):
    """A descriptor breaks its type's contract; carries every violation found."""

    def __init__(self, violations: tuple[Violation, ...] | list[Violation]) -> None:
        self.violations: tuple[Violation, ...] = tuple(violations)
        summary = "; ".join(str(v) for v in self.violations) or "no violations given"
        super().__init__(f"invalid descriptor: {summary}")


class IncompleteRollup(CrystaliaModelError):
    """A folder rollup was asked for with fewer children than the listing promised.

    ``reason`` is always ``INCOMPLETE``: this is a failed harvest, never a
    publishable descriptor state (ruling C1).
    """

    reason: str = ViolationCode.INCOMPLETE.value

    def __init__(self, expected: int, present: int, detail: str = "") -> None:
        self.expected = expected
        self.present = present
        msg = f"incomplete rollup: {present} of {expected} listed children present"
        super().__init__(f"{msg}; {detail}" if detail else msg)


class DegenerateCoverage(CrystaliaModelError):
    """``coverage_of`` cannot be computed: format and object length both unknown."""


class RegistryLoadError(CrystaliaModelError):
    """A type or format registry row is malformed; raised at load time."""


__all__ = [
    "CrystaliaModelError",
    "DegenerateCoverage",
    "IncompleteRollup",
    "InvalidDescriptor",
    "RegistryLoadError",
    "UnknownType",
    "Violation",
    "ViolationCode",
]
