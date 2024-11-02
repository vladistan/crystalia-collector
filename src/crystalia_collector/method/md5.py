from crystalia_collector.method.generic import GenericMethod


class MD5_8GB(GenericMethod):
  def __init__(self):
    super().__init__()
    self.id = "md5-8gb"
    self.block_size = 8 * 2 ** 30


class MD5_2GB(GenericMethod):
  def __init__(self):
    super().__init__()
    self.id = "md5-2gb"
    self.block_size = 2 * 2 ** 30


class MD5_Unbounded(GenericMethod):
  def __init__(self):
    super().__init__()
    self.id = "md5"


def method_by_id(method_id: str) -> GenericMethod:
  if method_id == "md5-8gb":
    return MD5_8GB()
  elif method_id == "md5-2gb":
    return MD5_2GB()
  elif method_id == "md5":
    return MD5_Unbounded()
  else:
    raise ValueError(f"Unknown method {method_id}. Supported methods: md5, md5-2gb, md5-8gb")
