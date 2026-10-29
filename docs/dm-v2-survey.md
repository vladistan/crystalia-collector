# DM v2 Surface Survey (plan 03, step 11.5)

Survey of what `crystalia-data-model` v2 the collector actually calls, as of the vendored copy at
`src/crystalia_data_model/VENDORED.md` (main@`5319a2a`, v2.1.1). Survey only — no code changes
follow from this document alone; see *Candidate gaps* below for change ideas, left as open
questions for vlad/crysDM to rule on.

## Descriptor and method inventory

| Collector file | DM module | Names used |
|---|---|---|
| `glimpse_compute.py` | `types.leaves` | `mint_filename`, `mint_file_size`, `mint_md5_region`, `mint_ctime`, `mint_mtime`, `mint_glimpse`, `mint_glimpse_slim`, `mint_glimpse_light`, `mint_glimpse_meta`, `mint_glimpse_content` |
| `glimpse_dir_compute.py` | `types.leaves`, `types.rollup` | `mint_filename`, `mint_mtime`, `mint_count`, `mint_glimpse_dir_meta`; `mint_glimpse_dir`, `mint_glimpse_dir_slim`, `mint_glimpse_dir_light`, `mint_glimpse_dir_content` |
| `bookend_compute.py` | `types.leaves`, `types.canonical`, `types.formats`, `types.zipdesc`, `types.bookend` | `mint_md5_region`, `mint_file_size`, `mint_format`; `mint_composite` (direct — see gap 1); `detect_format`, `Detection`; `mint_zip_cd`, `mint_zip_manifest`, `parse_central_directory`; `judge_bookend` (verdict only, not `mint_bookend` — see gap 1) |
| `bookend_dir_compute.py` | `types.bookend` | `mint_bookend_dir`, `DirEntry` |
| `work.py` | `types.leaves`, `types.coverage`, `types.provenance`, `types.registry`, `types.validate` | `mint_md5`, `mint_md5_region`, `mint_relpath`; `mint_md5_chunked`; `mint_method`, `record_harvest`; `default_registry`; `ensure_valid` |
| `merge.py` | `types.errors`, `types.provenance` | `IncompleteRollup`; `mint_method`, `record_harvest` |
| `rdf.py` | `datamodel.linkml_crystalia` | `Thing` (base class for the vendored RDF dumper/loader) |
| everywhere | `datamodel.linkml_crystalia` | `Descriptor`, `Item`, `Method`, `HarvestRecord` (stored pydantic classes; never hand-built except via `mint_*`/`record_harvest`) |

Methods/descriptor families actually emitted: `glimpse*` (5 file variants + `glimpse-content`),
`glimpse-dir*` (3 rollup variants + `glimpse-dir-content`, + `glimpse-dir-meta` composite),
`bookend-strong`/`bookend-weak`, `bookend-dir-strong`/`bookend-dir-weak`, `zip-cd`, `zip-manifest`,
`md5` / `md5-region` / `md5-chunked`, `relpath`. Not emitted: `asserted`, S3 ETag subtypes, any
`inferred` type (Lane D's `infer()` / `InferenceRule` are not called anywhere in the collector).

## Slot usage per descriptor type

- **Leaf scalars** (`filename`, `relpath`, `file-size`, `count`, `format`, `mtime`, `ctime`): one
  value string each, built from `FileObject`/directory stat fields; the collector never reads
  these back except to write them into `partials-manifest` lines (`work.py:151`, `hasType`/`value`
  only, informational, not a sameness decision).
- **`md5` / `md5-region`**: `value` = hex digest; `length` = bytes hashed; `offset` on the
  positional variant only. Chunk boundaries come from the collector's own task-file line format
  (`offset`, `block_size`), not from the DM.
- **`md5-chunked`**: built from a sorted list of `md5-region` parts; `total` = `len(ordered)`; gap
  detection (`expected_offset` contiguity) is collector logic *before* minting, not a DM check —
  the DM's own `present > total` / `total == 0` checks still run inside `mint_md5_chunked`.
- **Field composites** (`glimpse*`, `bookend-strong/weak`): built via role-kwarg dicts
  (`_FIELD_TO_ROLE` in `glimpse_compute.py`); the collector tracks its own field-name → DM-role
  mapping rather than reading `TypeEntry.children.roles` from the registry.
- **Rollups** (`glimpse-dir*`, `bookend-dir-*`): built from `(basename, child_descriptor)` pairs,
  bottom-up, deepest-directory-first (`glimpse_scanner.scan_with_dirs`,
  `bookend_scanner.scan_bookend_dirs`). `expected` is always the collector's own child count at
  scan time, never a separate listing (consumer contract point 7, honoured).
- **`Item`**: `label`, `hasDescriptor` (ids only), `isPartOf` (`None` for roots). Populated in
  `work.py:_build_directory_items` / `_build_file_items`.
- **`HarvestRecord`**: `startedAt`, `endedAt`, `collectorVersion`, `sourceRoot`, `usesMethod`,
  `hasRoot` — all six populated (`work.py:861`, `merge.py:103`). No `operator`/`hostname`/
  `cliOptions` slots exist in the DM today (see gap 3 / plan step 11.8).

## Validation contract points depended on

1. **`ensure_valid(desc, resolve=...)`** — called once per descriptor, but gated:
   `if desc.hasType in _dm_registry` (`work.py:471`). Types outside the registry are skipped, not
   rejected. See gap 2.
2. **`IncompleteRollup`** — caught nowhere; both `merge.py` (sidecar-count-vs-manifest check) and
   the DM's own `rollup_dir`/`mint_glimpse_dir*`/`mint_bookend_dir` let it propagate and abort the
   run (consumer contract point 7: an incomplete harvest fails, never silently continues).
3. **`default_registry()` / `Registry.__contains__`** — the only registry introspection the
   collector does; used solely to gate point 1's `ensure_valid` call, never for grade/strength
   decisions (those stay in the DM via `judge_bookend`, never reimplemented collector-side).
4. **Consumer contract point 1** (mint only via `canonical.mint_*` / `rollup_dir` / ...) — honoured
   everywhere except `bookend_compute.py:60`, which calls `mint_composite` directly instead of the
   DM's own `mint_bookend` (see gap 1).
5. **Consumer contract point 5** (`is_a`/`grade`/`is_strong`, never raw `hasType` string matching)
   — honoured; the two other `.hasType` reads are logging/registry-membership, not type decisions.

## Candidate gaps and change ideas (open questions, not committed work)

1. **`bookend_compute.py` re-derives `mint_bookend`'s internals instead of calling it.** The DM's
   `mint_bookend(head, tail, format, size, detection)` exists and does exactly this, but per its
   docstring/consumer-contract note, it "mints these same leaves internally but does not return
   them" — so the collector cannot get `head_d`/`tail_d`/etc. back to persist them, and re-does
   the head/tail/format/size minting plus the `bookend-strong`/`bookend-weak` type-name choice by
   hand. Open question: should `mint_bookend` return its children (a DM API change), or is the
   collector's duplication the intended shape and the DM's docstring should say so more loudly?
2. **The `ensure_valid` gate silently exempts non-registry types.** `relpath` and `md5-chunked`
   actually *are* in the registry (both are DM-minted — the `work.py:471` comment calling them
   "methods not yet migrated to DM minting" looks stale), so in practice every emitted type is
   checked today. But the gate itself has no visibility (no count, no log line) into whether it
   is skipping anything — if a future DM-minted type is accidentally built with a hand-rolled
   `Descriptor(...)` instead of a `mint_*` call, it would silently skip validation rather than
   fail loudly. Open question: tighten the gate to assert (not silently skip) once confirmed that
   every emitted type is registry-known, or keep it as a deliberate future-proofing escape hatch?
3. **`HarvestRecord` has no operator/hostname/cliOptions slots** — tracked separately as plan 03
   step 11.8 (tower-coordinate with tavuk-crysDM); flagged here for completeness, not re-opened.
4. **Collector-side role-kwarg maps (`_FIELD_TO_ROLE`) duplicate `TypeEntry.children.roles`.**
   The DM already carries each field composite's role names/order in the registry; the collector
   maintains a parallel hand-written mapping. Open question: worth reading role names from
   `default_registry().type_of(...).children.roles` instead, to remove one point of drift, or is
   the duplication cheap enough (5 glimpse variants, 3 glimpse-dir variants) not to bother?
5. **No `asserted`, ETag, or `inferred` emission** — consistent with the DM's own v2 scope (ETags
   "defined, not emitted"; inference is a DM-internal framework with no v2 collector caller).
   Not a gap against the DM; noted only so a future reader doesn't go looking for the call site.
