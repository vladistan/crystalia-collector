"""Build Glimpse file descriptors from a FileObject and a Source, via the DM leaf/composite mints."""

from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.source import FileObject, Source
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.leaves import (
    mint_ctime,
    mint_file_size,
    mint_filename,
    mint_glimpse,
    mint_glimpse_light,
    mint_glimpse_meta,
    mint_glimpse_slim,
    mint_md5_region,
    mint_mtime,
)

# field name (collector's variant field order) -> DM composite role kwarg name
_FIELD_TO_ROLE: dict[str, str] = {
    "filename": "filename",
    "size": "file_size",
    "md5": "head",
    "ctime": "ctime",
    "mtime": "mtime",
}

_COMPOSITE_MINTERS = {
    "glimpse": mint_glimpse,
    "glimpse-slim": mint_glimpse_slim,
    "glimpse-light": mint_glimpse_light,
    "glimpse-meta": mint_glimpse_meta,
}


def build_file_descriptor(
    file_obj: FileObject,
    method: GlimpseBase,
    source: Source,
) -> tuple[Descriptor, list[Descriptor]]:
    """Compute a Glimpse descriptor tree for a single file, minted by the DM.

    Returns (top_level_descriptor, child_descriptors). The caller is
    responsible for persisting both; hasDescriptor on the top level
    references child IDs (set by the DM composite mint).
    """
    file_size = file_obj.size
    block_size = method.block_size

    # Read first block_size bytes only if the variant includes md5
    md5_hex = source.compute_checksum(file_obj.uri, 0, block_size) if method.has_md5 else ""
    md5_length = min(block_size, file_size)

    mtime_str = file_obj.mtime.isoformat()
    # ctime is filesystem-only; absent on S3 objects
    ctime_str = file_obj.ctime.isoformat() if file_obj.ctime is not None else ""

    children: list[Descriptor] = []
    role_kwargs: dict[str, Descriptor] = {}
    for field in method.fields:
        if field == "filename":
            leaf = mint_filename(file_obj.basename)
        elif field == "size":
            leaf = mint_file_size(file_obj.size)
        elif field == "md5":
            leaf = mint_md5_region(0, md5_length, md5_hex)
        elif field == "ctime":
            leaf = mint_ctime(ctime_str)
        elif field == "mtime":
            leaf = mint_mtime(mtime_str)
        else:
            msg = f"unknown glimpse field {field!r}"
            raise ValueError(msg)
        children.append(leaf)
        role_kwargs[_FIELD_TO_ROLE[field]] = leaf

    top = _COMPOSITE_MINTERS[str(method.id)](**role_kwargs)
    return top, children
