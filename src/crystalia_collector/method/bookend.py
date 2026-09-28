"""Bookend and zip descriptor methods: format-aware, strength-graded comparison identity."""

from crystalia_collector.method.generic import GenericMethod

BOOKEND_BLOCK = 16384


class BookendBase(GenericMethod):
    """Base for bookend/zip file methods: reads a fixed head+tail window, never the whole file."""

    def __init__(self) -> None:
        super().__init__()
        self.block_size = BOOKEND_BLOCK

    @property
    def needs_offsets(self) -> bool:
        return False


class Bookend(BookendBase):
    """16 KB head + 16 KB tail + format + size, stored bookend-strong/bookend-weak per D-1."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "bookend"


class ZipCd(BookendBase):
    """Hash over the raw zip Central Directory bytes; not applicable to non-zip files."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "zip-cd"


class ZipManifest(BookendBase):
    """Comparison-grade hash over sorted (member name, CRC-32, size); not applicable to non-zip."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "zip-manifest"


class BookendDirBase(GenericMethod):
    """Base for the bookend directory rollup: no own fields, strong iff every child is strong."""

    def __init__(self) -> None:
        super().__init__()
        self.block_size = 0
        self.paired_file_method_id: str = "bookend"

    @property
    def needs_offsets(self) -> bool:
        return False


class BookendDir(BookendDirBase):
    """bookend-dir-strong/bookend-dir-weak rollup: zip-manifest children for zip files, else bookend."""

    def __init__(self) -> None:
        super().__init__()
        self.id = "bookend-dir"
