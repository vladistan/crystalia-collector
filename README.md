# Crystalia Collector

Generate dataset descriptors for large S3-hosted datasets as RDF annotations.

For architecture, extensibility, and infrastructure details see [docs/architecture.md](docs/architecture.md).

## Installation

```bash
uv sync
```

## Usage

```bash
# List files in an S3 prefix
crystalia-collector list my-bucket/path/to/data

# List and generate task files for parallel processing
crystalia-collector list my-bucket/path/to/data --task-dir ./tasks --method-id md5-8gb

# Compute checksum for a single S3 object
crystalia-collector checksum s3://my-bucket/path/to/file.gz

# Compute checksum for a byte range
crystalia-collector checksum s3://my-bucket/path/to/file.gz --offset 0 --length 8589934592

# Process a task file and generate RDF annotations
crystalia-collector annotate tasks/task_1 --output-file annotations.rdf

# Combine annotations (placeholder — not yet implemented)
crystalia-collector combine
```

## Checksum Methods

| Method ID | Block Size | Description |
|-----------|------------|-------------|
| `md5` | Unbounded | MD5 of the entire file |
| `md5-2gb` | 2 GB | MD5 in 2 GB blocks |
| `md5-8gb` | 8 GB | MD5 in 8 GB blocks (default) |

Block-based methods split large files into offset/length pairs in task files, enabling parallel checksum computation.

## Configuration

Settings load in this order (highest priority first):

1. Environment variables (`CRYSTALIA_*` prefix, or bare `SENTRY_DSN`)
2. `./crystalia.toml` in the current directory
3. `~/.config/crystalia-collector/config.toml`
4. Built-in defaults

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CRYSTALIA_DEFAULT_METHOD_ID` | `md5-8gb` | Checksum method |
| `CRYSTALIA_DEFAULT_OUTPUT_FILE` | `out.rdf` | Output file for annotations |
| `CRYSTALIA_ENABLE_TELEMETRY` | `false` | Send crash reports to Sentry |
| `CRYSTALIA_SENTRY_DSN` | project default | Override Sentry DSN |
| `SENTRY_DSN` | — | Bare DSN fallback |
| `CRYSTALIA_LOG_JSON` | `true` | JSON-formatted log output |
| `AWS_PROFILE` | `default` | AWS credentials profile |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |

### Config File

```toml
# crystalia.toml or ~/.config/crystalia-collector/config.toml
default_method_id = "md5-8gb"
default_output_file = "out.rdf"
enable_telemetry = false
log_json = false
```

Copy `.envrc.example` to `.envrc` and adjust as needed.

## Docker

```bash
docker build -t crystalia-collector .
docker run --rm crystalia-collector --help
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
```

## License

MIT
