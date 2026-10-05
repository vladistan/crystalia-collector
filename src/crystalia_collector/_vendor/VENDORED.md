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

## Local patch: `pydantic_rdf_loader.py` graph-free bulk API (2026-10-04)

crysUI's viz loader parses RDF via pyoxigraph, not rdflib, so it has no `Graph`
to hand `dict_from_subject_triples` — only a subject's own `(predicate_iri,
object)` pairs. Added `dict_from_pairs(target_class, subject, pairs,
prefix_map=None) -> dict[str, Any]`: the same field-name resolution, literal
coercion, and list-handling as `dict_from_subject_triples`, but driven by pairs
instead of a graph walk, and with no nested-model recursion (there is no graph
to check a referenced URI's own triples, so every IRI object is always
converted to its CURIE form). The literal-value conversion (datatype/language
coercion) was factored out of `_convert_object_value` into a shared
`_convert_literal_value` so both paths use the same logic.
`crystalia_collector.rdf.dict_from_pairs` wraps it with the project's
CURIE-expansion convention.

This file is **no longer byte-identical to its vendored source commit** —
apply this patch again after any re-vendor from upstream, until it is
upstreamed (see TODO below).

## Local patch: `pydantic_rdf_loader.py` dict_from_pairs perf (2026-10-05)

crysUI profiled `dict_from_pairs` at ~61µs/subject -- doubling their viz load
time (set-a 50s -> 99s) -- because every call redid work that only depends on
`target_class`: scanning every field to resolve a predicate (`_find_field_for_
predicate`), re-deriving prefixes/global metadata, and re-running `typing.get_
origin`/`get_args` introspection for the multilingual and list-wrap passes.
Added a per-`target_class` profile, cached on the loader instance (`_pairs_
profile`/`_pairs_profile_cache`): a precomputed predicate-IRI -> field-name map
(`_build_predicate_to_field_map`), resolved prefixes, and per-field type kinds
for two new fast equivalents (`_apply_multilingual_fast`, `_apply_list_wrap_
fast`) that only touch fields actually present in `model_data` instead of
iterating every model field. Also added a small `_uri_to_curie_cached` memo.
Output is unchanged -- `dict_from_pairs`'s existing tests all still pass
unmodified. `crystalia_collector.rdf.dict_from_pairs` now goes through an
`@lru_cache`d singleton loader (`_pairs_loader()`) instead of a fresh
`PydanticRDFLoader()` per call, since the whole point of the cache is useless
against a new, empty instance every time. Measured: ~45µs/subject with a fresh
instance per call (the old effective behavior) down to ~3.2µs/subject on a
warm, reused loader -- under crysUI's ≤5µs/subject target.

This file is **no longer byte-identical to its vendored source commit** —
apply this patch again after any re-vendor from upstream, until it is
upstreamed (see TODO below).

## TODO — remove this vendoring

- [ ] Upstream `PydanticRDFDumper` / `PydanticRDFLoader` into public
      `linkml-runtime`, including the IRI-emission and bulk-API patches above.
- [ ] Once released on PyPI, delete this directory and import the classes from
      `linkml_runtime` again (see `crystalia_collector/rdf.py`).
