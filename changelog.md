# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-29

Breaking release: the collector emits crystalia-data-model (DM) v2. Every
collection produced by 0.x is invalid under DM v2. Local collections are
re-collected; S3-published outputs are re-harvested after this release.

Supersession: the 0.3.0 interim fix at main@c3c507918fc5f0eddb43733b71450ff2b63baec3
(FR-011, no per-file `coverage` on md5-head) is superseded by the forward
migration to DM v2, not reverted.

### Breaking
- DM v2 IRIs: every descriptor IRI changes. Descriptors are minted by the
  vendored DM `types/` package, not by collector code.
- No `coverage` slot on descriptors. `offset` appears only on positional
  descriptors.
- Chunked md5 parts assemble into one md5-chunked region per file, with
  `total` set to the part count. The tail chunk records its true length.
- Fail-closed harvests: any failed task fails the run and writes nothing
  to the central output. `--fail-fast` is removed. `--partials-dir` (on
  `run` and `annotate`) writes a patch-up manifest on failure.
- The local schema copy is removed. The schema comes from the vendored DM
  package.

### Added
- New methods: `glimpse-content`, `glimpse-dir-content`, `bookend`,
  `bookend-dir`, `zip-cd`, `zip-manifest`.
- Harvest provenance: one `HarvestRecord` per successful run, linked to
  shared `Method` nodes and the root Items.
- `merge` command: combines `annotate` partition outputs into one DM-valid
  catalog with one harvest record.
- `--exclude` path filter on `run` and `list`.
- Sentry performance tracing (plan 03 step 11.7). `run` and `annotate` open
  one `cli` transaction. `run_pipeline` adds a `method` span per method
  (tag `method=<id>`) and a `task_file` span per `ProcessPoolExecutor.submit`.
  The trace header goes to the worker, which joins the same trace and emits
  one `file.read` span per file. Failures mark the active span
  `internal_error` before `capture_exception`.
- Verification: `run` on 96 real files (`.claude/patterns/code`) with
  `md5-8gb` + `glimpse`, local envelope sink, sample rate 1.0. Span tree:
  `run` (trace 9385b774) -> `method md5-8gb` -> `task_file task_1`;
  `method glimpse`. Worker transaction `task_1` has the same trace id,
  parent = the `task_file` span, 96 `file.read` children.

### Changed
- **Breaking consumer contract:** re-vendored crystalia-data-model v2.1.0
  (namespace split). Type-registry CURIEs move from `cryd:desc-type/<name>`
  to `crys:dtype/<name>`; every content-addressed descriptor id changes
  (the type CURIE is hashed into the id). Item ids now default to
  `cryd:<uuid>` (was `crys:<uuid>`) — `cryd:` is instance-data-only
  (descriptors and items); `crys:` is reserved for type/schema CURIEs.
  Every existing collection is invalid under this namespace; re-harvest.

## [0.3.0] - 2026-09-25

### Changed
- FR-011: md5-head (and md5-Ngb chunk) descriptors no longer carry per-file
  `coverage` (content-addressed nodes carry only facts derived from
  type+value). Consumers derive md5-head coverage = min(length / file-size, 1).
  Vendored crystalia-data-model @57639cf: Descriptor.coverage optional.

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
