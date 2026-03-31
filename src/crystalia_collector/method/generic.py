class GenericMethod:
    def __init__(self) -> None:
        self.block_size = 0
        self.id: str | None = None

    @property
    def needs_offsets(self) -> bool:
        return self.block_size != 0
