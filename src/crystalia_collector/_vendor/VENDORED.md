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

## Local patch: `pydantic_rdf_dumper.py` IRI emission (2026-09-30)

`_emit_value` emitted a `URIRef` only for a nested `BaseModel` field value.
Id-reference slots whose Python type is a plain `str` (`hasDescriptor`,
`isPartOf`, `hasType`, `hasRoot`, `usesMethod` — CURIEs identifying another
entity, not inline data) fell through to `_to_rdf_literal` and serialized as
`xsd:string` literals instead of `URIRef`s: a write-side asymmetry, since
`PydanticRDFLoader` and `ensure_valid(resolve=...)` already treat these as
references on read. Patched to consult the slot's `linkml_meta` `range`: a
scalar range (`string`, `integer`, `boolean`, `date`, `datetime`, ...) still
serializes as a literal; any other range (`uriorcurie`, `uri`, or a class name
like `Item`/`Method`) now emits `URIRef(expand_curie(value))`.

This file is **no longer byte-identical to its vendored source commit** —
apply this patch again after any re-vendor from upstream, until it is
upstreamed (see TODO below).

## Local patch: `pydantic_rdf_loader.py` public bulk API (2026-10-04)

`PydanticRDFLoader` only exposed `load()`, which instantiates a full Pydantic
model per subject. crysUI needed a cheaper bulk-extraction path (CURIE/value
lookups across many subjects) and was calling two private methods
(`_find_field_for_predicate` plus typing introspection) to reconstruct it
themselves. Added a public `dict_from_subject_triples(graph, subject,
target_class, prefix_map=None) -> dict[str, Any]`: field-name resolution and
per-triple value conversion (the same work `load()` does per subject), minus
model instantiation/shell/cache machinery. `_convert_subject_to_model` was
refactored to share this logic via a new private `_subject_to_dict` helper, so
the two paths cannot drift. `crystalia_collector.rdf.dict_from_subject` wraps
it with the project's CURIE-expansion convention, mirroring `model_from_rdf`.

This file is **no longer byte-identical to its vendored source commit** —
apply this patch again after any re-vendor from upstream, until it is
upstreamed (see TODO below).

## TODO — remove this vendoring

- [ ] Upstream `PydanticRDFDumper` / `PydanticRDFLoader` into public
      `linkml-runtime`, including the IRI-emission and bulk-API patches above.
- [ ] Once released on PyPI, delete this directory and import the classes from
      `linkml_runtime` again (see `crystalia_collector/rdf.py`).
