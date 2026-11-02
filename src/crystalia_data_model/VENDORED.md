# Vendored package: `crystalia_data_model`

**Source:** `crystalia-data-model` main@`8720b54` (v2.1.1 + 3 commits, untagged)
(`HarvestRecord` gains optional `operator`, `hostname`, `cliOptions` slots;
`Registry.type_of`/`ancestors`/`is_a` memoized; `cryd:` prefix resolves under
w3id.org as of v2.1.1; internal plan/requirement refs scrubbed from docstrings)
(`src/crystalia_data_model/`, the LinkML-generated Pydantic data model plus
the `types/` behaviour package, at `../crystalia-data-model`).

**Tree hash:** `867626ed3c9528d8087bcec01a1d47102f1109a8d9aa85ba48552b062a682907`
(`tests/test_vendored_dm.py::vendored_tree_hash`, sorted relative paths and
file bytes fed into one SHA-256 digest, `__pycache__` excluded).

**License:** MIT (crystalia-data-model upstream license). Compatible with this
project's Apache-2.0 license.

**Why vendored:** `crystalia-data-model` is not published on PyPI, so it
cannot be resolved as a normal dependency of a public `crystalia-collector`
release. The vendored tree depends only on the standard library and
`pydantic`, so inlining it is self-contained.

## Contents (do not hand-edit — generated or type-hierarchy source)

- `__init__.py`, `__about__.py`
- `datamodel/__init__.py`, `datamodel/linkml_crystalia.py` — generated Pydantic model
- `schema/linkml_crystalia.yaml` — LinkML schema, single source for `rdf.py` CURIE expansion
- `types/` — descriptor type hierarchy, canonical content-addressed identity,
  coverage/robustness, format detection, inference, provenance, rollup

## Re-vendor procedure

1. In `../crystalia-data-model`, cut and tag the new release.
2. `git archive <tag> -- src/crystalia_data_model | tar -x` into a scratch dir,
   copy its contents over `src/crystalia_data_model/` here (this file excluded).
3. Recompute the tree hash and update the **Tree hash:** line above and the
   **Source:** tag/commit above.
4. `uv run pytest tests/test_vendored_dm.py`.
