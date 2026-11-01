# CLAUDE.md

## Project

crystalia-collector — CLI tool that generates RDF dataset descriptors from large S3-hosted and local datasets.

## Structure

```
src/crystalia_collector/
  app.py            # Typer CLI entry point (list, annotate, checksum, combine, run, merge, test-sentry)
  config.py         # Pydantic Settings (env vars, TOML files)
  work.py           # Core workflow: list dirs, generate tasks, compute annotations, run pipeline
  merge.py          # merge: combine annotate partitions into one DM-valid catalog + harvest record
  scan_paths.py     # Path scanning and exclusion helpers
  bookend_*.py      # bookend / bookend-dir descriptor scanners
  s3_iface.py       # Legacy S3 facade (delegates to source/s3.py)
  rdf.py            # RDF <-> Pydantic model conversion via PydanticRDFDumper/Loader
  glimpse_scanner.py     # Walks a source and scans files/dirs with a Glimpse method
  glimpse_compute.py     # Computes file-level Glimpse descriptors (content ids)
  glimpse_dir_compute.py # Computes directory-level Glimpse descriptors
  monitoring.py     # Sentry + structlog setup
  util.py           # Size formatting, offset generation, task file writing
  _vendor/          # Vendored fork RDF code (PydanticRDFDumper/Loader) — see VENDORED.md
  source/           # Source abstraction layer
    __init__.py     # FileObject model, Source protocol, detect_source()
    local.py        # LocalSource: local filesystem backend
    s3.py           # S3Source: AWS S3 backend
  method/           # Descriptor computation methods
    __init__.py     # Method registry and method_by_id() factory
    generic.py      # GenericMethod base class
    glimpse.py      # Glimpse variants (full, slim, light, meta)
    glimpse_dir.py  # GlimpseDir variants (directory-level descriptors)
    md5.py          # MD5 variants (unbounded, 2GB, 8GB)
```

## Data Model

Pydantic models are imported from `crystalia_data_model.datamodel.linkml_crystalia`.
For public PyPI distribution this package is **vendored** into
`src/crystalia_data_model/` (source of truth: `../crystalia-data-model`; see its
`VENDORED.md`). RDF conversion uses `PydanticRDFDumper`/`PydanticRDFLoader`, also
**vendored** into `src/crystalia_collector/_vendor/` because they exist only in
the LinkML monorepo fork, not in public `linkml-runtime`. Public
`linkml-runtime` still supplies `SchemaView` and the vendored classes' base
classes.

## CLI Commands

```bash
crystalia-collector list <prefix> [--task-dir D] [--method-id M] [--exclude P]  # List files; with --task-dir also writes task files + listing_manifest.json
crystalia-collector annotate <task-file> [--output-file F] [--partials-dir D]   # Descriptors for one task file; writes F and F.sidecar
crystalia-collector checksum <uri> [--offset N] [--length N]                    # Checksum of a single file
crystalia-collector combine <dir> -o <out> [-f turtle|text]                     # Combine per-item Turtle files into one catalog
crystalia-collector run <source> [-o out] [--method M]... [-w N] [--partials-dir D] [--exclude P]...  # Local end-to-end pipeline; fail-closed
crystalia-collector merge <listing-manifest> <partition.ttl>... -o <out> [--root R] [--method M]...      # Merge annotate partitions; one harvest record
crystalia-collector test-sentry                                                 # Send a test event to Sentry
```

`run` and `annotate` are fail-closed (no `--fail-fast`). `merge` checks each
directory's entry count against the listing manifest and aborts on a short
partition. Operator procedures: `docs/runbook.md`.

## Development Commands

```bash
uv sync                          # Install dependencies
uv run pytest                    # Run tests
uv run ruff check .              # Lint
uv run mypy .                    # Type check (strict, files=".")
docker build -t crystalia-collector .  # Build container
```

## Key Details

- Version 1.0.0; DM v2 output (breaking vs 0.x; see changelog.md)
- Python 3.13+, hatchling build backend, uv for dependency management
- Entry point: `crystalia-collector` -> `crystalia_collector.app:app`
- Coverage minimum: 80%
- MyPy strict mode enabled
- S3 tests require real AWS credentials (skipped automatically when unavailable)
- Tests ignore `legacy/` and `data_model/` directories
- Nextflow pipelines in `pipelines/`, Pulumi infrastructure in `infrastructure/`
