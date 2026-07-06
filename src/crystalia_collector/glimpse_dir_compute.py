"""Build Glimpse directory descriptors by aggregating child descriptors (files or dirs)."""

import hashlib
from datetime import datetime

from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

_TYPE_FILENAME = "cryd:desc-type/filename"
_TYPE_MTIME = "cryd:desc-type/mtime"
_TYPE_COUNT = "cryd:desc-type/count"


def _descriptor_id(hash_hex: str) -> str:
    return f"cryd:{hash_hex}"


def _content_id(type_uri: str, value: str) -> str:
    """Stable content-addressable ID: cryd:<md5(type_uri:value)>."""
    return _descriptor_id(hashlib.md5(f"{type_uri}:{value}".encode()).hexdigest())


def _build_child_descriptor(type_uri: str, value: str) -> Descriptor:
    return Descriptor(
        id=_content_id(type_uri, value),
        hasType=type_uri,
        value=value,
        offset=0,
        coverage=1.0,
    )


def _rollup_v0(
    dir_field_values: dict[str, str],
    field_order: tuple[str, ...],
    child_descriptors: list[tuple[str, Descriptor]],
) -> str:
    """Compute v0 rollup hash for a directory.

    dir_field_values: dir's own field values (filename, mtime, count)
    field_order: dir variant's own fields (e.g. ("filename", "mtime", "count"))
    child_descriptors: list of (basename, top-level descriptor) pairs for all direct
                       children (files or subdirectories), sorted by basename.

    Input format: dir's own fields (fieldname:value\\n), then each child as
    child:<basename>:<child_v0_hash>\\n.
    Returns 'v0:<md5_hex>'.
    """
    lines = "".join(f"{f}:{dir_field_values[f]}\n" for f in field_order)
    for basename, child_desc in child_descriptors:
        lines += f"child:{basename}:{child_desc.value}\n"
    return f"v0:{hashlib.md5(lines.encode()).hexdigest()}"


def build_dir_descriptor(
    dir_basename: str,
    dir_mtime: datetime,
    method: GlimpseDirBase,
    child_descriptors: list[tuple[str, Descriptor]],
) -> tuple[Descriptor, list[Descriptor]]:
    """Compute a Glimpse descriptor tree for a directory.

    child_descriptors: list of (basename, top-level descriptor) pairs for all direct
        children — files or subdirectories. Must be pre-sorted by basename.

    Returns (top_level_descriptor, child_metadata_descriptors).
    """
    child_count = len(child_descriptors)
    mtime_str = dir_mtime.isoformat()
    count_str = str(child_count)

    dir_field_values: dict[str, str] = {
        "filename": dir_basename,
        "mtime": mtime_str,
        "count": count_str,
    }

    children: list[Descriptor] = []
    for field in method.fields:
        if field == "filename":
            children.append(_build_child_descriptor(_TYPE_FILENAME, dir_basename))
        elif field == "mtime":
            children.append(_build_child_descriptor(_TYPE_MTIME, mtime_str))
        elif field == "count":
            children.append(_build_child_descriptor(_TYPE_COUNT, count_str))

    # Rollup hash (all non-meta dir variants)
    composite_value: str
    if method.has_rollup:
        composite_value = _rollup_v0(dir_field_values, method.fields, child_descriptors)
    else:
        # glimpse-dir-meta: composite over dir's own fields only, no children
        lines = "".join(f"{f}:{dir_field_values[f]}\n" for f in method.fields)
        composite_value = f"v0:{hashlib.md5(lines.encode()).hexdigest()}"

    top_hash = composite_value.removeprefix("v0:")
    top = Descriptor(
        id=_descriptor_id(top_hash),
        hasType=f"cryd:{method.id}",
        value=composite_value,
        offset=0,
        coverage=1.0,
        hasDescriptor=[c.id for c in children],
    )
    return top, children
