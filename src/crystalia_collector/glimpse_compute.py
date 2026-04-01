"""Build Glimpse file descriptors from a FileObject and a Source."""

import hashlib
from collections.abc import Sequence

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.source import FileObject, Source

# Child descriptor type URIs (cryd: = data-instance namespace)
_TYPE_FILENAME = "cryd:desc-type/filename"
_TYPE_FILE_SIZE = "cryd:desc-type/file-size"
_TYPE_MTIME = "cryd:desc-type/mtime"
_TYPE_CTIME = "cryd:desc-type/ctime"
_TYPE_MD5_HEAD = "cryd:desc-type/md5-head"

_FIELD_TYPE: dict[str, str] = {
    "filename": _TYPE_FILENAME,
    "size": _TYPE_FILE_SIZE,
    "mtime": _TYPE_MTIME,
    "ctime": _TYPE_CTIME,
    "md5": _TYPE_MD5_HEAD,
}


def _descriptor_id(hash_hex: str) -> str:
    return f"cryd:{hash_hex}"


def _content_id(type_uri: str, value: str) -> str:
    """Stable content-addressable ID: cryd:<md5(type_uri:value)>."""
    return _descriptor_id(hashlib.md5(f"{type_uri}:{value}".encode()).hexdigest())


def _build_child_descriptor(
    type_uri: str,
    value: str,
    coverage: float,
    length: int | None = None,
) -> Descriptor:
    return Descriptor(
        id=_content_id(type_uri, value),
        hasType=type_uri,
        value=value,
        offset=0,
        coverage=coverage,
        length=length,
    )


def _composite_v0(field_values: dict[str, str], field_order: Sequence[str]) -> str:
    """Compute v0 composite hash over field_values in fixed field_order.

    Input format: one 'fieldname:value\\n' line per field, in the given order.
    Returns 'v0:<md5_hex>'.
    """
    lines = "".join(f"{f}:{field_values[f]}\n" for f in field_order)
    return f"v0:{hashlib.md5(lines.encode()).hexdigest()}"


def build_file_descriptor(
    file_obj: FileObject,
    method: GlimpseBase,
    source: Source,
) -> tuple[Descriptor, list[Descriptor]]:
    """Compute a Glimpse descriptor tree for a single file.

    Returns (top_level_descriptor, child_descriptors). The caller is
    responsible for persisting both; hasDescriptor on the top level
    references child IDs.
    """
    file_size = file_obj.size
    block_size = method.block_size

    # Read first block_size bytes only if the variant includes md5
    md5_hex = source.compute_checksum(file_obj.uri, 0, block_size) if method.has_md5 else ""
    md5_coverage = min(block_size / file_size, 1.0) if file_size > 0 else 1.0
    md5_length = min(block_size, file_size)

    mtime_str = file_obj.mtime.isoformat()
    # ctime is filesystem-only; absent on S3 objects
    ctime_str = file_obj.ctime.isoformat() if file_obj.ctime is not None else ""

    field_raw: dict[str, str] = {
        "filename": file_obj.basename,
        "size": str(file_obj.size),
        "md5": md5_hex,
        "mtime": mtime_str,
        "ctime": ctime_str,
    }

    children: list[Descriptor] = []
    for field in method.fields:
        type_uri = _FIELD_TYPE[field]
        value = field_raw[field]
        if field == "md5":
            child = _build_child_descriptor(type_uri, value, md5_coverage, md5_length)
        else:
            child = _build_child_descriptor(type_uri, value, 1.0)
        children.append(child)

    composite_value = _composite_v0(field_raw, method.fields)
    top_coverage = md5_coverage if method.has_md5 else 1.0
    top_hash = composite_value.removeprefix("v0:")

    top = Descriptor(
        id=_descriptor_id(top_hash),
        hasType=f"cryd:{method.id}",
        value=composite_value,
        offset=0,
        coverage=top_coverage,
        hasDescriptor=[c.id for c in children],
    )
    return top, children
