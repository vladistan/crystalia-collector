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

Settings are loaded in this order (highest priority first):

1. Environment variables (`CRYSTALIA_*` prefix, or bare `SENTRY_DSN`)
2. `./crystalia.toml` in the current directory
3. `~/.config/crystalia-collector/config.toml` (user global)
4. Built-in defaults

### Config file

Create `~/.config/crystalia-collector/config.toml` for persistent settings:

```toml
default_method_id = "md5-8gb"
sentry_environment = "production"
log_json = false
enable_telemetry = true
```

### Environment variables

| Variable | Description |
|----------|-------------|
| `AWS_PROFILE` | AWS credentials profile to use |
| `AWS_DEFAULT_REGION` | AWS region (e.g. `us-east-1`) |
| `CRYSTALIA_ENABLE_TELEMETRY` | Send crash reports to Sentry (default: `true`) |
| `CRYSTALIA_SENTRY_DSN` | Override Sentry DSN (uses project default when not set) |
| `SENTRY_DSN` | Bare DSN fallback, e.g. for CI or Heroku |
| `CRYSTALIA_DEFAULT_METHOD_ID` | Default checksum method (default: `md5-8gb`) |
| `CRYSTALIA_DEFAULT_OUTPUT_FILE` | Default output file for annotations (default: `out.rdf`) |
| `CRYSTALIA_LOG_JSON` | JSON-formatted log output (default: `true`) |

Copy `.envrc.example` to `.envrc` and adjust as needed.

To disable telemetry: `export CRYSTALIA_ENABLE_TELEMETRY=false`

## Telemetry

Crystalia Collector reports errors and performance data to Sentry by default (`enable_telemetry=true`). No personally identifiable information is collected.

To verify your Sentry integration is working:

```bash
crystalia-collector test-sentry
```

To redirect telemetry to your own Sentry project:

```bash
export CRYSTALIA_SENTRY_DSN=https://your-key@your-org.ingest.sentry.io/your-project
```

To disable telemetry entirely:

```bash
export CRYSTALIA_ENABLE_TELEMETRY=false
```

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
