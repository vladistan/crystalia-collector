"""Lane D rows: inferred equivalence types and the name-hint type (SPARC D-6).

Each inference rule emits its own named type so that inferred facts never merge with
harvested ones. Rows here are the v2 data-only set plus the single name-hint type; Lane D
may refine them.
"""

from __future__ import annotations

from crystalia_data_model.types.registry import Grade, Robustness, TypeEntry, inferred

_PENDING = "robustness: SPARC default (weakest link of the inputs), pending Lane D"

ROWS: tuple[TypeEntry, ...] = (
    inferred(
        "md5-from-small-glimpse",
        ("glimpse-content",),
        Grade.COMPARISON,
        Robustness.LOW,
        doc=f"a glimpse-content whose file-size <= 2 KB pins the whole file: equivalent to md5; {_PENDING}",
    ),
    inferred(
        "md5-equals-md5-region",
        ("md5", "md5-region"),
        Grade.COMPARISON,
        Robustness.VERY_HIGH,
        strong=True,
        doc=f"whole-file md5 <-> md5-region(0, size) equivalence (an inference, never an IRI collapse); {_PENDING}",
    ),
    inferred(
        "bookend-chunked-agreement",
        ("bookend-strong", "bookend-weak", "md5-chunked"),
        Grade.COMPARISON,
        Robustness.MODERATE,
        doc=f"bookend head/tail agree with md5-chunked parts; {_PENDING}",
    ),
    inferred(
        "bookend-strong-by-name",
        ("bookend-weak",),
        Grade.COMPARISON,
        Robustness.LOW,
        doc="name-hint: extension suggests a strong family; lower robustness, never merged with a verified bookend-strong",
    ),
)

__all__ = ["ROWS"]
