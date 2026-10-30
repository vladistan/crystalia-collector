"""Security review checks (plan 03 step 11.3): provenance root and credential leaks."""

import re
import shutil
from pathlib import Path

import pytest
from rdflib import Graph, URIRef
from typer.testing import CliRunner

from crystalia_collector.app import app

CRYS_SOURCE_ROOT = URIRef("https://w3id.org/crystalia/sourceRoot")
DUMMY_KEY_ID = "AKIAZZZZZZZZZZZZZZZZ"
DUMMY_SECRET = "dummySecretAccessKey0123456789ABCDEFGHIJ"
DUMMY_TOKEN = "dummySessionToken0123456789"
CREDENTIAL_SHAPES = re.compile(r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|aws_secret|aws_access_key|SessionToken")
RECORDED = Path(__file__).parent / "recorded"


@pytest.fixture
def harvest(tmp_path, monkeypatch):
    """Run `run` on real recorded files with dummy S3 credentials in the environment."""
    root = tmp_path / "corpus"
    root.mkdir()
    for ttl in sorted(RECORDED.glob("*.ttl"))[:3]:
        shutil.copy(ttl, root / ttl.name)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", DUMMY_KEY_ID)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", DUMMY_SECRET)
    monkeypatch.setenv("AWS_SESSION_TOKEN", DUMMY_TOKEN)
    out = tmp_path / "out.ttl"
    result = CliRunner().invoke(app, ["run", str(root), "--method", "glimpse", "--workers", "1", "-o", str(out)])
    assert result.exit_code == 0, result.output
    return root, out, result.output


def test_provenance_source_root_is_the_root_as_given(harvest):
    root, out, _ = harvest
    graph = Graph()
    graph.parse(out, format="turtle")
    roots = {str(o) for o in graph.objects(predicate=CRYS_SOURCE_ROOT)}
    assert roots == {str(root)}


def test_output_has_no_path_beyond_the_source_root(harvest, tmp_path):
    root, out, _ = harvest
    text = out.read_text()
    outside = [m for m in re.findall(r'"(/[^"]+)"', text) if not m.startswith(str(root))]
    assert outside == []
    assert str(Path.home()) not in text


def test_no_credentials_in_output_logs_or_files(harvest, tmp_path):
    _, out, console = harvest
    leaked = [DUMMY_KEY_ID, DUMMY_SECRET, DUMMY_TOKEN]
    blobs = [out.read_text(), console, *(p.read_text(errors="ignore") for p in tmp_path.rglob("*") if p.is_file())]
    for blob in blobs:
        assert not any(secret in blob for secret in leaked)
        assert CREDENTIAL_SHAPES.search(blob) is None
