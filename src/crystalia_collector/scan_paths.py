"""Shared path helpers for scanning local/S3 trees bottom-up."""

from pathlib import Path


def resolve_root(root_prefix: str) -> str:
    """Resolve a scan root to the same canonical form LocalSource uses for file URIs.

    LocalSource resolves every file path (symlinks included) before yielding it, so
    callers comparing a root prefix against those URIs must resolve the root the same
    way -- otherwise a symlink anywhere in the root's path (e.g. macOS /tmp ->
    /private/tmp) breaks every string-prefix/length comparison against it.
    """
    if root_prefix.startswith("s3://"):
        return root_prefix
    return str(Path(root_prefix).resolve())


def parent_uri(uri: str) -> str:
    """Return the parent directory URI (local or S3), without trailing slash."""
    if uri.startswith("s3://"):
        return uri.rsplit("/", 1)[0]
    return str(Path(uri).parent)


def dir_basename(dir_uri: str) -> str:
    """Return just the directory name, stripped of path prefix."""
    if dir_uri.startswith("s3://"):
        return dir_uri.rstrip("/").rsplit("/", 1)[-1]
    return Path(dir_uri).name or dir_uri


def ancestor_uris(uri: str, root_prefix: str) -> list[str]:
    """Return all ancestor directory URIs from uri up to and including root_prefix.

    root_prefix is resolved once via resolve_root so this comparison matches uri's
    resolved form (LocalSource always yields resolved URIs); otherwise a symlink
    anywhere in root_prefix's path breaks that match and this over- or under-climbs.
    """
    root = resolve_root(root_prefix)
    ancestors: list[str] = []
    current = uri
    while True:
        parent = parent_uri(current)
        if parent == current or len(parent) < len(root):
            break
        if parent not in ancestors:
            ancestors.append(parent)
        current = parent
    return ancestors
