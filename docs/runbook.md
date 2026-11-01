# Operator Runbook

## Choose a flow

| Source | Flow |
|--------|------|
| Local directory | `run` (one process) |
| S3 or large partitioned harvest | `list --task-dir` → `annotate` per task file → `merge` |

## Single pass: `run`

```bash
crystalia-collector run /abs/path/data -o catalog.ttl --method md5-8gb --partials-dir ./partials
```

The source must be an absolute path; relative paths are rejected. `run` writes `catalog.ttl` only if every file hashed. The output is written to a
temp file and renamed on success. On any failure the output path stays untouched
and the exit code is non-zero.

## Partitioned flow

1. `crystalia-collector list s3://bucket/prefix --task-dir ./tasks --method-id md5-8gb`
   writes task files and `tasks/listing_manifest.json`.
2. For each task file: `crystalia-collector annotate tasks/task_N --output-file out_N.ttl --partials-dir ./partials`.
   Each run writes `out_N.ttl` and `out_N.ttl.sidecar`.
3. `crystalia-collector merge tasks/listing_manifest.json out_*.ttl -o catalog.ttl --root s3://bucket/prefix --method md5-8gb`.

`merge` compares each directory's entry count with the listing manifest. A
short partition aborts the merge and nothing is written. `merge` emits one
`HarvestRecord`.

## Failure policy

Every harvest is fail-closed. One unhashed entry fails the whole command.
Nothing reaches the central output.

| Symptom | Cause | Action |
|---------|-------|--------|
| Exit 1, `harvest incomplete` | Some entries did not hash | Patch up (below) |
| Exit 1, unknown descriptor type or id mismatch | Internal inconsistency | Do not retry. Report with the structured log line. A Sentry event is sent if `SENTRY_DSN` is set |
| `merge` count mismatch | A partition is missing or short | Re-run the missing `annotate`, then `merge` again |

## Patch-up flow

With `--partials-dir D`, a failed `run` or `annotate` writes `D/partials_manifest.txt`.
It holds first the task-file lines that did not hash, then the descriptors
already completed.

1. Copy the failed lines into a new task file.
2. Run `annotate` on that task file to a new partition output.
3. Run `merge` with the original partitions plus the new one.

`--partials-dir` must not equal or contain the output path. It does not accept an S3 URI.
The partials manifest is never uploaded on its own.

## Harvest record

Each successful `run` or `merge` emits one `HarvestRecord` with start/end
time, collector version, source root, `operator`, `hostname` and `cliOptions`.
`annotate` emits none. A failed harvest emits none.

## Release

Certification and publish follow `OPS-PUBLISH-001`. Publish only on explicit
go-ahead from the maintainer. The vendored `src/crystalia_data_model/` tree hash
in its `VENDORED.md` must match `tests/test_vendored_dm.py::vendored_tree_hash`.
