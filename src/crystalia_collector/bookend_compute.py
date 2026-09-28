"""Build bookend/zip-cd/zip-manifest file descriptors from a FileObject and a Source, via the DM."""

import hashlib

from crystalia_collector.method.bookend import BOOKEND_BLOCK
from crystalia_collector.source import FileObject, Source
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.bookend import judge_bookend
from crystalia_data_model.types.canonical import mint_composite
from crystalia_data_model.types.formats import Detection, detect_format
from crystalia_data_model.types.leaves import mint_file_size, mint_format, mint_md5_region
from crystalia_data_model.types.zipdesc import mint_zip_cd, mint_zip_manifest, parse_central_directory


def _read_head_tail(file_obj: FileObject, source: Source) -> tuple[bytes, bytes | None]:
    head = source.read_head(file_obj.uri, BOOKEND_BLOCK)
    tail = source.read_tail(file_obj.uri, BOOKEND_BLOCK) if file_obj.size > BOOKEND_BLOCK else None
    return head, tail


def detect(file_obj: FileObject, source: Source) -> tuple[bytes, bytes | None, Detection]:
    """Read the head/tail window and run DM format detection over it."""
    head, tail = _read_head_tail(file_obj, source)
    return head, tail, detect_format(head, tail, file_obj.size)


def _cd_bytes(file_obj: FileObject, head: bytes, tail: bytes | None, detection: Detection) -> bytes | None:
    """Central Directory bytes when ``detection`` located them wholly inside the tail, else None."""
    if detection.rule_applied != "cd_in_tail" or detection.summary_region is None:
        return None
    cd_offset, cd_size = detection.summary_region
    tail_bytes = tail if tail is not None else head
    tail_start = max(0, file_obj.size - BOOKEND_BLOCK) if tail is not None else 0
    start = cd_offset - tail_start
    return tail_bytes[start : start + cd_size]


def build_bookend_descriptor(file_obj: FileObject, source: Source) -> tuple[Descriptor, list[Descriptor]]:
    """Bookend descriptor tree: head/tail md5-region + format + size leaves, composed into
    ``bookend-strong``/``bookend-weak`` per the DM's D-1 verdict (``judge_bookend``).

    Returns (top, children) like ``glimpse_compute.build_file_descriptor`` — the DM's own
    ``mint_bookend`` mints these same leaves internally but does not return them, so they are
    minted here directly (via the DM's leaf helpers) to keep them persistable.
    """
    head, tail, detection = detect(file_obj, source)
    tail_bytes = tail if tail is not None else head
    size = file_obj.size
    head_len = min(BOOKEND_BLOCK, size)
    tail_start = max(0, size - BOOKEND_BLOCK)
    tail_len = size - tail_start

    head_d = mint_md5_region(0, head_len, hashlib.md5(head).hexdigest())
    tail_d = mint_md5_region(tail_start, tail_len, hashlib.md5(tail_bytes).hexdigest())
    size_d = mint_file_size(size)
    format_d = mint_format(detection.format_id or "")

    verdict = judge_bookend(size, detection)
    type_name = "bookend-strong" if verdict.strong else "bookend-weak"
    top = mint_composite(type_name, {"head": head_d, "tail": tail_d, "format": format_d, "file-size": size_d})
    return top, [head_d, tail_d, size_d, format_d]


def build_zip_cd_descriptor(file_obj: FileObject, source: Source) -> Descriptor | None:
    """``zip-cd`` descriptor, or None when the file is not a zip with its CD inside the tail."""
    head, tail, detection = detect(file_obj, source)
    cd_bytes = _cd_bytes(file_obj, head, tail, detection)
    if cd_bytes is None:
        return None
    return mint_zip_cd(cd_bytes)


def build_zip_manifest_descriptor(file_obj: FileObject, source: Source) -> Descriptor | None:
    """``zip-manifest`` descriptor, or None when the file is not a zip with its CD inside the tail."""
    head, tail, detection = detect(file_obj, source)
    cd_bytes = _cd_bytes(file_obj, head, tail, detection)
    if cd_bytes is None:
        return None
    members = parse_central_directory(cd_bytes)
    return mint_zip_manifest(members)
