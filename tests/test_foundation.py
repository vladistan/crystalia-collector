"""Phase 1 — Foundation Modernization tests.

Step 1.1: Import path spike and schema relocation.
Step 1.2: Configuration extension (default_workers, default_format).
"""

import os
from pathlib import Path

import pytest

# --- Step 1.1: Import path spike ---


def test_linkml_runtime_schemaview_imports():
    from linkml_runtime import SchemaView

    assert SchemaView is not None


def test_linkml_runtime_rdflib_dumper_imports():
    from linkml_runtime.dumpers import RDFLibDumper

    assert RDFLibDumper is not None


def test_linkml_runtime_rdflib_loader_imports():
    from linkml_runtime.loaders import RDFLibLoader

    assert RDFLibLoader is not None


def test_crystalia_data_model_item_imports():
    from crystalia_data_model.datamodel.linkml_crystalia import Item

    assert Item is not None


def test_crystalia_data_model_all_types_import():
    from crystalia_data_model.datamodel.linkml_crystalia import (
        Descriptor,
        Item,
        Method,
        Thing,
    )

    assert all(cls is not None for cls in [Descriptor, Item, Method, Thing])


def test_schema_loads_from_vendored_location():
    from linkml_runtime import SchemaView

    schema_path = (
        Path(__file__).parent.parent / "src" / "crystalia_data_model" / "schema" / "linkml_crystalia.yaml"
    )
    sv = SchemaView(schema=str(schema_path))
    assert "Item" in sv.all_classes()
    assert "Descriptor" in sv.all_classes()


def test_rdf_module_schema_loads():
    from crystalia_collector.rdf import get_schema

    schema = get_schema()
    assert "Item" in schema.all_classes()


def test_get_schema_curies_expand_to_same_iris():
    from crystalia_collector.rdf import get_schema

    schema = get_schema()
    assert schema.expand_curie("crys:Item") == "https://w3id.org/crystalia/Item"
    assert schema.expand_curie("cryd:abc123") == "https://crystalia.link/data/abc123"


# --- Step 1.2: Configuration extension ---


def test_default_workers_defaults_to_cpu_count():
    from crystalia_collector.config import CollectorSettings

    settings = CollectorSettings()
    expected = (os.cpu_count() or 1) * 2
    assert settings.default_workers == expected


def test_default_format_defaults_to_turtle():
    from crystalia_collector.config import CollectorSettings

    settings = CollectorSettings()
    assert settings.default_format == "turtle"


def test_default_format_accepts_text(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_DEFAULT_FORMAT", "text")
    from crystalia_collector.config import CollectorSettings

    settings = CollectorSettings()
    assert settings.default_format == "text"


def test_default_format_rejects_invalid(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_DEFAULT_FORMAT", "json")
    from crystalia_collector.config import CollectorSettings

    with pytest.raises(ValueError):
        CollectorSettings()
