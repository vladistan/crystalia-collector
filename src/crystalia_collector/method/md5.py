from crystalia_collector.method.generic import GenericMethod


class MD5_8GB(GenericMethod):  # noqa: N801
    def __init__(self) -> None:
        super().__init__()
        self.id = "md5-8gb"
        self.block_size = 8 * 2**30


class MD5_2GB(GenericMethod):  # noqa: N801
    def __init__(self) -> None:
        super().__init__()
        self.id = "md5-2gb"
        self.block_size = 2 * 2**30


class MD5_Unbounded(GenericMethod):
    def __init__(self) -> None:
        super().__init__()
        self.id = "md5"
