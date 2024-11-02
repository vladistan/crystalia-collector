class GenericMethod:
  def __init__(self):
    self.block_size = 0
    self.id = None

  @property
  def needs_offsets(self):
    return self.block_size != 0
