"""Method registry: factory for all descriptor computation methods."""

from crystalia_collector.method.generic import GenericMethod
from crystalia_collector.method.glimpse import Glimpse, GlimpseLight, GlimpseMeta, GlimpseSlim
from crystalia_collector.method.glimpse_dir import (
    GlimpseDir,
    GlimpseDirLight,
    GlimpseDirMeta,
    GlimpseDirSlim,
)
from crystalia_collector.method.md5 import MD5_2GB, MD5_8GB, MD5_Unbounded

_METHODS: dict[str, type[GenericMethod]] = {
    "md5": MD5_Unbounded,
    "md5-2gb": MD5_2GB,
    "md5-8gb": MD5_8GB,
    "glimpse": Glimpse,
    "glimpse-slim": GlimpseSlim,
    "glimpse-light": GlimpseLight,
    "glimpse-meta": GlimpseMeta,
    "glimpse-dir": GlimpseDir,
    "glimpse-dir-slim": GlimpseDirSlim,
    "glimpse-dir-light": GlimpseDirLight,
    "glimpse-dir-meta": GlimpseDirMeta,
}


def method_by_id(method_id: str) -> GenericMethod:
    """Return a method instance for the given method identifier."""
    if method_id not in _METHODS:
        supported = ", ".join(sorted(_METHODS))
        msg = f"Unknown method '{method_id}'. Supported: {supported}"
        raise ValueError(msg)
    return _METHODS[method_id]()
