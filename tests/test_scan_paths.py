from crystalia_collector.scan_paths import ancestor_uris, resolve_root


def test_resolve_root_resolves_symlink(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real_dir)

    assert resolve_root(str(link)) == str(real_dir.resolve())


def test_resolve_root_passes_through_s3_uri():
    assert resolve_root("s3://bucket/prefix") == "s3://bucket/prefix"


def test_ancestor_uris_stops_at_symlinked_root(tmp_path):
    """Regression: comparing an unresolved root against resolved file URIs by raw
    string length over-climbs past the intended root whenever the root's path
    contains a symlink (e.g. macOS /tmp -> /private/tmp), pulling in unrelated
    ancestor directories above it.
    """
    real_dir = tmp_path / "real"
    (real_dir / "sub").mkdir(parents=True)
    link_root = tmp_path / "link_root"
    link_root.symlink_to(real_dir)

    file_uri = str((real_dir / "sub" / "a.txt").resolve())
    ancestors = ancestor_uris(file_uri, str(link_root))

    assert ancestors == [str((real_dir / "sub").resolve()), str(real_dir.resolve())]
