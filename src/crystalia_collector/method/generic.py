class GenericMethod:
    def __init__(self) -> None:
        self.block_size = 0
        self.id: str | None = None

    @property
    def needs_offsets(self) -> bool:
        return self.block_size != 0

    def parameters(self) -> dict[str, str]:
        """Canonical parameters for this method's content-addressed ``Method`` node."""
        return {"block_size": str(self.block_size)}
