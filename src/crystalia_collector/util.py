

from typing import Generator


def human_readable_size(size_bytes: int) -> str:
    if size_bytes >= 2**50:
        return f"{size_bytes / (2**50):.1f} PB"
    elif size_bytes >= 2**40:
        return f"{size_bytes / (2**40):.1f} TB"
    elif size_bytes >= 2**30:
        return f"{size_bytes / (2**30):.1f} GB"
    elif size_bytes >= 2**20:
        return f"{size_bytes / (2**20):.1f} MB"
    elif size_bytes >= 2**10:
        return f"{size_bytes / (2**10):.1f} KB"
    else:
        return f"{size_bytes}"

def stream_offsets(blocksize: int, length: int) -> Generator[int, None, None]:
    for offset in range(0, length, blocksize):
        yield offset