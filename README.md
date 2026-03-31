# Crystalia Collector

Generate dataset descriptors for large datasets stored in S3.

Crystalia Collector is a CLI tool that lists files in S3 buckets, computes checksums (MD5), generates task files for parallel processing, and produces RDF annotations. It is part of the [Crystalia](https://github.com/Ebiquity/crystalia-collector) project.

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

# Compute checksum for a single file
crystalia-collector checksum s3://my-bucket/path/to/file.gz

# Compute checksum for a byte range
crystalia-collector checksum s3://my-bucket/path/to/file.gz --offset 0 --length 8589934592

# Process a task file and generate RDF annotations
crystalia-collector annotate tasks/task_1 --output-file annotations.rdf

# Combine all annotations into a single file
crystalia-collector combine
```

## Checksum Methods

| Method ID | Block Size | Description |
|-----------|------------|-------------|
| `md5` | Unbounded | MD5 of the entire file |
| `md5-2gb` | 2 GB | MD5 computed in 2 GB blocks |
| `md5-8gb` | 8 GB | MD5 computed in 8 GB blocks (default) |

The block-based methods generate offset/length pairs in task files, enabling parallel checksum computation for large objects.

## Configuration

Environment variables:

| Variable | Description |
|----------|-------------|
| `AWS_PROFILE` | AWS credentials profile to use |
| `AWS_DEFAULT_REGION` | AWS region (e.g. `us-east-1`) |
| `SENTRY_DSN` | Sentry DSN for error tracking (optional) |
| `CRYSTALIA_DEFAULT_METHOD_ID` | Default checksum method (default: `md5-8gb`) |
| `CRYSTALIA_DEFAULT_OUTPUT_FILE` | Default output file for annotations (default: `out.rdf`) |
| `CRYSTALIA_LOG_JSON` | Enable JSON-formatted log output |

Copy `.envrc.example` to `.envrc` and adjust as needed.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
```

## Docker

```bash
docker build -t crystalia-collector .
docker run --rm crystalia-collector --help
```

## License

MIT
