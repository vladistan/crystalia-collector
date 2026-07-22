"""Glimpse directory descriptor methods: structural change detection with optional rollup."""

from crystalia_collector.method.generic import GenericMethod

# Composite hash field orders per variant (fixed, never sorted — see design spec)
_GLIMPSE_DIR_FIELDS: tuple[str, ...] = ("filename", "mtime", "count")
_GLIMPSE_DIR_SLIM_FIELDS: tuple[str, ...] = ("filename", "mtime")
_GLIMPSE_DIR_LIGHT_FIELDS: tuple[str, ...] = ("mtime",)
_GLIMPSE_DIR_META_FIELDS: tuple[str, ...] = ("filename", "mtime", "count")


class GlimpseDirBase(GenericMethod):
    """Base for Glimpse directory methods: aggregates child file descriptors."""

    def __init__(self) -> None:
        super().__init__()
        self.block_size = 0
        self.fields: tuple[str, ...] = ()
        self.has_rollup: bool = True
        self.paired_file_method_id: str = ""
        self.robustness: str = "LOW"

    @property
    def needs_offsets(self) -> bool:
        return False


class GlimpseDir(GlimpseDirBase):
    """Full dir glimpse: filename, mtime, count + rollup from glimpse. Robustness: LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-dir"
        self.fields = _GLIMPSE_DIR_FIELDS
        self.paired_file_method_id = "glimpse"


class GlimpseDirSlim(GlimpseDirBase):
    """Slim dir glimpse: filename, mtime + rollup from glimpse-slim. Robustness: LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-dir-slim"
        self.fields = _GLIMPSE_DIR_SLIM_FIELDS
        self.paired_file_method_id = "glimpse-slim"


class GlimpseDirLight(GlimpseDirBase):
    """Light dir glimpse: mtime + rollup from glimpse-light. Robustness: VERY_LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-dir-light"
        self.fields = _GLIMPSE_DIR_LIGHT_FIELDS
        self.paired_file_method_id = "glimpse-light"
        self.robustness = "VERY_LOW"


class GlimpseDirMeta(GlimpseDirBase):
    """Meta dir glimpse: filename, mtime, count (no rollup). Robustness: VERY_LOW."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "glimpse-dir-meta"
        self.fields = _GLIMPSE_DIR_META_FIELDS
        self.has_rollup = False
        # Paired with the metadata-only file method so directory children can be
        # enumerated and counted. With has_rollup=False the file descriptors are
        # only used for the child count, never folded into the directory hash.
        self.paired_file_method_id = "glimpse-meta"
        self.robustness = "VERY_LOW"
