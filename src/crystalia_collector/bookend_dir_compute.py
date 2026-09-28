"""Build the bookend-dir rollup descriptor from already-chosen child D-3 candidates, via the DM."""

from collections.abc import Iterable

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.bookend import DirEntry, mint_bookend_dir


def build_bookend_dir_descriptor(expected: int, entries: Iterable[DirEntry]) -> Descriptor:
    """``bookend-dir-strong``/``bookend-dir-weak`` rollup over each child's chosen candidate (D-3/D-4)."""
    return mint_bookend_dir(expected, entries)
