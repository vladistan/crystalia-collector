class MD5Generic:
    def __init__(self):
        pass


class MD5_8GB(MD5Generic):
    def __init__(self):
        super().__init__()
        self.block_size
        self.block_size = 8 * 2**30
        self.needs_offsets = True


class MD5_2GB(MD5Generic):
    def __init__(self):
        super().__init__()
        self.id = "md5_2gb"
        self.block_size = 2 * 2**30
        self.needs_offsets = True


class MD5_Unbounded:
    def __init__(self):
        super().__init__()
        self.id = "md5"
        self.need_offsets = False
