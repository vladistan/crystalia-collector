# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-22

### Added
- Emit a `cryd:desc-type/relpath` descriptor on every file Item, carrying the
  file's path relative to the scan root (e.g. `dir1/.DS_Store`). This is
  location metadata attached at the Item level and is deliberately **not** part
  of any content-composite hash, so content descriptor IDs are unchanged and
  identical files in different directories still share content IDs. Resolves a
  downstream request (CRYSTALIA-VIZ-01): two files that share a basename in
  different directories are now distinguishable by path. Back-compatible —
  consumers fall back to the basename `filename` descriptor when relpath is
  absent in older collections.

### Fixed
- Corrected `isPartOf` in the bundled `schema/crystalia.yaml` from
  `required: true` to `required: false`, matching the upstream
  crystalia-data-model schema and the generated Pydantic model (which the plain
  glimpse path relies on when emitting `isPartOf`-less file Items).
- `glimpse-dir-meta` no longer crashes with `Unknown method ''`. It had an empty
  `paired_file_method_id`; it is now paired with `glimpse-meta` so directories
  are enumerated and emit `count`/`mtime` descriptors (no rollup, as intended).

## [0.1.1] - 2026-07-05

First public release on PyPI.

### Added
- Vendored the `crystalia_data_model` Pydantic data model (MIT) so the package
  installs from public PyPI without the unpublished `crystalia-data-model`
  dependency. See `src/crystalia_data_model/VENDORED.md`.
- Vendored the `PydanticRDFDumper` / `PydanticRDFLoader` RDF modules (CC0-1.0)
  used by `crystalia_collector.rdf`; these exist only in the LinkML monorepo
  fork and are not yet in public `linkml-runtime`. See
  `src/crystalia_collector/_vendor/VENDORED.md`.

### Changed
- Packaging is now self-contained: removed the `[tool.uv.sources]` local
  editable paths (`crystalia-data-model`, `linkml`, `linkml-runtime`).
- Dependencies pinned to public PyPI releases: `linkml-runtime>=1.11`, plus
  explicit `pydantic>=2`, `rdflib>=6.0`, `hbreader>=0.9`. Dropped the unused
  top-level `linkml` (compiler/generators) dependency — only `linkml_runtime`
  is used at runtime.
- Corrected the license classifier to Apache-2.0 to match the bundled `LICENSE`.
- Pinned Docker base images and the `uv` build tool to fixed versions.
- Repaired the CI workflow to use `uv` on Python 3.13 (was `pip install '.[dev]'`
  against a non-existent extra on Python 3.11).

### Internal
- Refactored `work.run_pipeline` to extract `_build_directory_items` and
  `_build_file_items` helpers (no behavior change).
- Documented the rationale for lazy in-function imports.

### TODO
- Upstream `PydanticRDFDumper` / `PydanticRDFLoader` into public
  `linkml-runtime`, then drop `src/crystalia_collector/_vendor/`.

## [0.1.0] - 2024-07-25

- First release.
