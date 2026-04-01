"""Glimpse file descriptor methods: fast change detection via first-2KB MD5 + metadata."""

from crystalia_collector.method.generic import GenericMethod

# Composite hash field orders per variant (fixed, never sorted — see design spec)
_GLIMPSE_FIELDS: tuple[str, ...] = ("filename", "size", "md5", "ctime", "mtime")
_GLIMPSE_SLIM_FIELDS: tuple[str, ...] = ("filename", "size", "mtime", "md5")
_GLIMPSE_LIGHT_FIELDS: tuple[str, ...] = ("size", "md5", "mtime")
_GLIMPSE_META_FIELDS: tuple[str, ...] = ("filename", "size", "mtime")


class GlimpseBase(GenericMethod):
    """Base for Glimpse file methods: reads first block_size bytes, never chunks."""

    def __init__(self) -> None:
        super().__init__()
        self.block_size = 2048
        self.fields: tuple[str, ...] = ()
        self.robustness: str = "LOW"

    @property
    def needs_offsets(self) -> bool:
        return False

    @property
    def has_md5(self) -> bool:
        return "md5" in self.fields


class Glimpse(GlimpseBase):
    """Full glimpse: filename, size, MD5-head, ctime, mtime. Robustness: LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse"
        self.fields = _GLIMPSE_FIELDS


class GlimpseSlim(GlimpseBase):
    """Slim glimpse: filename, size, mtime, MD5-head (no ctime). Robustness: LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-slim"
        self.fields = _GLIMPSE_SLIM_FIELDS


class GlimpseLight(GlimpseBase):
    """Light glimpse: size, MD5-head, mtime (no name, no ctime). Robustness: VERY_LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-light"
        self.fields = _GLIMPSE_LIGHT_FIELDS
        self.robustness = "VERY_LOW"


class GlimpseMeta(GlimpseBase):
    """Meta glimpse: filename, size, mtime (no MD5). Robustness: VERY_LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-meta"
        self.fields = _GLIMPSE_META_FIELDS
        self.robustness = "VERY_LOW"
