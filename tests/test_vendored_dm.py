"""Guards the vendored DM v2.0.0 tree against silent drift."""

import hashlib
import subprocess
import zipfile
from pathlib import Path

VENDOR_ROOT = Path(__file__).parent.parent / "src" / "crystalia_data_model"
VENDORED_MD = VENDOR_ROOT / "VENDORED.md"


def vendored_tree_hash(root: Path) -> str:
    files = sorted(
        p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "VENDORED.md"
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _recorded_hash() -> str:
    text = VENDORED_MD.read_text()
    for line in text.splitlines():
        if line.startswith("**Tree hash:**"):
            return line.split("`")[1]
    raise AssertionError("VENDORED.md has no **Tree hash:** line")


def test_tree_hash_matches_vendored_md():
    assert vendored_tree_hash(VENDOR_ROOT) == _recorded_hash()


def test_types_public_names_importable():
    from crystalia_data_model import types

    for name in ("mint_glimpse", "mint_glimpse_dir", "default_registry", "validate"):
        assert hasattr(types, name)


def test_schema_yaml_present_in_built_wheel(tmp_path):
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        check=True,
        cwd=Path(__file__).parent.parent,
    )
    (wheel,) = tmp_path.glob("*.whl")
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    assert any(n.endswith("crystalia_data_model/schema/linkml_crystalia.yaml") for n in names)
