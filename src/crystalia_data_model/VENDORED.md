# Vendored package: `crystalia_data_model`

**Source:** `crystalia-data-model` v0.0.1 (`src/crystalia_data_model/`), the
LinkML-generated Pydantic data model that lives at `../crystalia-data-model`.

**License:** MIT (crystalia-data-model upstream license). Compatible with this
project's Apache-2.0 license.

**Why vendored:** `crystalia-data-model` is not published on PyPI, so it cannot
be resolved as a normal dependency of a public `crystalia-collector` release.
The generated model (`datamodel/linkml_crystalia.py`) depends only on the
standard library and `pydantic`, so inlining it is self-contained.

## Contents (do not hand-edit — generated)

- `__init__.py`, `__about__.py`
- `datamodel/__init__.py`
- `datamodel/linkml_crystalia.py` — generated Pydantic model

## TODO — keep in sync / remove this vendoring

- [ ] Source of truth is `../crystalia-data-model` (schema:
      `src/crystalia_data_model/schema/linkml_crystalia.yaml`). Regenerate there,
      then re-copy the four files above if the model changes.
- [ ] If `crystalia-data-model` is ever published to PyPI, delete this directory
      and depend on it normally.
