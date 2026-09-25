# Vendored package: `crystalia_data_model`

**Source:** `crystalia-data-model` v0.0.1 (`src/crystalia_data_model/`), the
LinkML-generated Pydantic data model that lives at `../crystalia-data-model`.

**Vendored at:** commit `57639cf634421c2b79f4a08edbebc02b61c7ae00`
(branch `fr011-coverage-optional`, "feat: make Descriptor.coverage optional
(FR-011 content-address invariant)"). The four files below are byte-identical
to `git show 57639cf:src/crystalia_data_model/<path>`. This snapshot also
carries upstream `86ec1e2` (`hasDescriptor` / `hasType` / `usesMethod` ranges
changed from class references to `uriorcurie` in `linkml_meta`; Python
annotations were already `str`, unchanged).

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
