# Vendored code

## `pydantic_rdf_dumper.py`, `pydantic_rdf_loader.py`

**Source:** `linkml_runtime.dumpers.pydantic_rdf_dumper` and
`linkml_runtime.loaders.pydantic_rdf_loader` from the LinkML monorepo fork
(`linkml-runtime` v1.10.0rc5.dev, ~2026-02).

**License:** CC0-1.0 (linkml-runtime upstream license).

**Why vendored:** `PydanticRDFDumper` / `PydanticRDFLoader` provide RDF
serialization for LinkML-generated Pydantic models directly from embedded
`linkml_meta`, without a `SchemaView`. They exist only in the local fork and are
**not present in public PyPI `linkml-runtime`** (latest public 1.11.1 ships only
`RDFDumper` / `RDFLibDumper`). `crystalia_collector.rdf` depends on them, so
without vendoring a public install would `ImportError` at runtime.

These modules import only their public base classes
(`linkml_runtime.dumpers.dumper_root.Dumper`,
`linkml_runtime.loaders.loader_root.Loader`,
`linkml_runtime.utils.yamlutils.YAMLRoot`) plus `pydantic`, `rdflib`, and
`hbreader` — all available in public `linkml-runtime>=1.11`.

## TODO — remove this vendoring

- [ ] Upstream `PydanticRDFDumper` / `PydanticRDFLoader` into public
      `linkml-runtime`.
- [ ] Once released on PyPI, delete this directory and import the classes from
      `linkml_runtime` again (see `crystalia_collector/rdf.py`).
