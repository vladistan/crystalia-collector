"""Build Glimpse directory descriptors by aggregating child descriptors (files or dirs), via the DM."""

from datetime import datetime

from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.leaves import mint_count, mint_filename, mint_glimpse_dir_meta, mint_mtime
from crystalia_data_model.types.rollup import mint_glimpse_dir, mint_glimpse_dir_light, mint_glimpse_dir_slim

_ROLLUP_MINTERS = {
    "glimpse-dir": mint_glimpse_dir,
    "glimpse-dir-slim": mint_glimpse_dir_slim,
    "glimpse-dir-light": mint_glimpse_dir_light,
}


def build_dir_descriptor(
    dir_basename: str,
    dir_mtime: datetime,
    method: GlimpseDirBase,
    child_descriptors: list[tuple[str, Descriptor]],
    expected: int | None = None,
) -> tuple[Descriptor, list[Descriptor]]:
    """Compute a Glimpse directory descriptor tree, minted by the DM.

    child_descriptors: list of (basename, top-level descriptor) pairs for all direct
        children — files or subdirectories.
    expected: entry count from the directory's own listing; defaults to
        ``len(child_descriptors)`` when the caller has no separate listing count.
        A rollup with fewer children than ``expected`` raises ``IncompleteRollup``.

    Returns (top_level_descriptor, child_metadata_descriptors).
    """
    mtime_str = dir_mtime.isoformat()
    count = len(child_descriptors)
    exp = count if expected is None else expected

    own_fields: dict[str, Descriptor] = {}
    children: list[Descriptor] = []
    for field in method.fields:
        if field == "filename":
            leaf = mint_filename(dir_basename)
        elif field == "mtime":
            leaf = mint_mtime(mtime_str)
        elif field == "count":
            leaf = mint_count(count)
        else:
            msg = f"unknown glimpse-dir field {field!r}"
            raise ValueError(msg)
        own_fields[field] = leaf
        children.append(leaf)

    if not method.has_rollup:
        # glimpse-dir-meta: composite over the dir's own fields only, no rollup children
        top = mint_glimpse_dir_meta(**own_fields)
        return top, children

    top = _ROLLUP_MINTERS[str(method.id)](exp, child_descriptors, **own_fields)
    return top, children
