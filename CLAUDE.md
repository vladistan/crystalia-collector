# CLAUDE.md

## Project

crystalia-collector — CLI tool that generates RDF dataset descriptors from large S3-hosted datasets.

## Structure

```
src/crystalia_collector/
  app.py            # Typer CLI entry point
  config.py         # Pydantic Settings (env vars, TOML files)
  work.py           # Core workflow: list S3, generate tasks, compute annotations
  s3_iface.py       # S3 client: paginated listing, byte-range checksums
  rdf.py            # RDF <-> LinkML model conversion via rdflib
  monitoring.py     # Sentry + structlog setup
  util.py           # Size formatting, offset generation, task file writing
  method/           # Checksum methods (GenericMethod base, MD5 variants)
  data/linkml/      # Vendored LinkML schema + generated dataclass model
```

## Data Model

The LinkML schema and generated Python model in `data/linkml/` are vendored from the
`crystalia-data-model` project (editable install via `uv.sources` in pyproject.toml).
After changes to the upstream schema, re-vendor the generated files.

## Commands

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
- Tests ignore `legacy/` and `data_model/` directories
- Nextflow pipelines in `pipelines/`, Pulumi infrastructure in `infrastructure/`
