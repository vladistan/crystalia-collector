# CLAUDE.md

## Project

crystalia-collector — CLI tool that generates RDF dataset descriptors from large S3-hosted and local datasets.

## Structure

```
src/crystalia_collector/
  app.py            # Typer CLI entry point (list, annotate, checksum, combine, run)
  config.py         # Pydantic Settings (env vars, TOML files)
  work.py           # Core workflow: list dirs, generate tasks, compute annotations, run pipeline
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
  schema/           # Local LinkML schema (crystalia.yaml, used for CURIE expansion)
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
crystalia-collector list <prefix>           # List files at S3 or local prefix
crystalia-collector annotate <task-file>    # Compute descriptors from task file
crystalia-collector checksum <uri>          # Compute checksum for a single file
crystalia-collector combine <dir> -o <out>  # Combine descriptor files into one
crystalia-collector run <prefix>            # End-to-end pipeline: list -> tasks -> annotate -> combine
```

## Development Commands

```bash
uv sync                          # Install dependencies
uv run pytest                    # Run tests
uv run ruff check .              # Lint
uv run mypy .                    # Type check (strict, files=".")
docker build -t crystalia-collector .  # Build container
```

## Key Details

- Python 3.13+, hatchling build backend, uv for dependency management
- Entry point: `crystalia-collector` -> `crystalia_collector.app:app`
- Coverage minimum: 80%
- MyPy strict mode enabled
- S3 tests require real AWS credentials (skipped automatically when unavailable)
- Tests ignore `legacy/` and `data_model/` directories
- Nextflow pipelines in `pipelines/`, Pulumi infrastructure in `infrastructure/`
