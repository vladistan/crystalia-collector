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
        DescriptorType,
        Item,
        Method,
        Thing,
    )

    assert all(cls is not None for cls in [Descriptor, DescriptorType, Item, Method, Thing])


def test_schema_loads_from_new_location():
    from linkml_runtime import SchemaView

    schema_path = Path(__file__).parent.parent / "src" / "crystalia_collector" / "schema" / "crystalia.yaml"
    sv = SchemaView(schema=str(schema_path))
    assert "Item" in sv.all_classes()
    assert "Descriptor" in sv.all_classes()


def test_rdf_module_schema_loads():
    from crystalia_collector.rdf import get_schema

    schema = get_schema()
    assert "Item" in schema.all_classes()


def test_schema_dir_points_to_existing_file():
    from crystalia_collector.rdf import SCHEMA_DIR

    schema_file = SCHEMA_DIR / "crystalia.yaml"
    assert schema_file.exists(), f"Schema file not found at {schema_file}"


def test_schema_dir_is_under_package():
    from crystalia_collector.rdf import SCHEMA_DIR

    assert "crystalia_collector" in SCHEMA_DIR.parts


def test_get_schema_missing_file_raises(tmp_path, monkeypatch):
    import crystalia_collector.rdf as rdf_mod

    rdf_mod.get_schema.cache_clear()
    monkeypatch.setattr(rdf_mod, "SCHEMA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        rdf_mod.get_schema()
    monkeypatch.undo()
    rdf_mod.get_schema.cache_clear()


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
