"""Merge partitioned task-file harvests into one complete, DM-valid output (Ph9).

Each partition comes from `annotate`: a Turtle file of DM v2 descriptors plus a
`(dir, name, child IRI)` sidecar (RDF carries no rollup name/child pairs, DM
consumer contract deviation 1). `merge` groups sidecar entries by directory,
checks each directory's entry count against the listing manifest's expected
count, then builds the same Item graph `run_pipeline` would for a single pass.
"""

from __future__ import annotations

import os
from pathlib import Path

from crystalia_collector import __version__
from crystalia_collector.method import method_by_id
from crystalia_collector.work import (
    ItemIdFactory,
    _build_directory_items,
    _build_file_items,
    _default_item_id,
    combine_descriptors,
    load_listing_manifest,
)
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.errors import IncompleteRollup
from crystalia_data_model.types.provenance import mint_method, record_harvest


def load_sidecar(sidecar_path: Path) -> list[tuple[str, str, str]]:
    """Return `(dir_uri, basename, descriptor_id)` rows from an `annotate` sidecar."""
    rows: list[tuple[str, str, str]] = []
    for line in sidecar_path.read_text().splitlines():
        if not line.strip():
            continue
        dir_uri, name, desc_id = line.split("\t")
        rows.append((dir_uri, name, desc_id))
    return rows


def load_descriptors(ttl_path: Path) -> dict[str, Descriptor]:
    """Load every `crys:Descriptor` subject from a partition's Turtle output, keyed by id."""
    from rdflib import Graph, Namespace

    from crystalia_collector.rdf import model_from_rdf

    crys = Namespace("https://w3id.org/crystalia/")
    g = Graph()
    g.parse(ttl_path, format="turtle")
    descriptors: dict[str, Descriptor] = {}
    for subject in g.subjects(crys.hasType, None):
        desc = model_from_rdf(g, Descriptor, subject=str(subject))
        assert isinstance(desc, Descriptor)
        descriptors[str(desc.id)] = desc
    return descriptors


def merge(
    listing_manifest_path: Path,
    partition_outputs: list[Path],
    output_path: Path,
    root: str,
    method_ids: list[str],
    item_id_factory: ItemIdFactory | None = None,
) -> None:
    """Merge `annotate` partition outputs into one DM-valid catalog with one harvest record.

    Raises `IncompleteRollup` and writes nothing if any directory's sidecar entry
    count falls short of the listing manifest's expected count for it.
    """
    id_factory = item_id_factory or _default_item_id
    expected = load_listing_manifest(listing_manifest_path)

    all_descriptors: dict[str, Descriptor] = {}
    entries_by_dir: dict[str, dict[str, str]] = {}
    for ttl_path in partition_outputs:
        all_descriptors.update(load_descriptors(ttl_path))
        sidecar_path = Path(f"{ttl_path}.sidecar")
        for dir_uri, name, desc_id in load_sidecar(sidecar_path):
            entries_by_dir.setdefault(dir_uri, {})[name] = desc_id

    for dir_uri, present_expected in expected.items():
        present = len(entries_by_dir.get(dir_uri, {}))
        if present < present_expected:
            raise IncompleteRollup(present_expected, present)

    merged_files: dict[str, list[Descriptor]] = {}
    for dir_uri in sorted(entries_by_dir):
        for name, desc_id in sorted(entries_by_dir[dir_uri].items()):
            uri = str(Path(dir_uri) / name)
            merged_files[uri] = [all_descriptors[desc_id]]

    # Task-file mode never produces directory-level (glimpse-dir) descriptors, so
    # merge builds file Items only, matching run_pipeline's own shape for the
    # non-GlimpseDir methods task-file mode is used for.
    dir_items, dir_item_ids, dir_relpath_descriptors = _build_directory_items({}, id_factory, root)
    file_items, relpath_descriptors = _build_file_items(merged_files, dir_item_ids, root, id_factory)
    items = dir_items + file_items
    descriptors = list(all_descriptors.values()) + dir_relpath_descriptors + relpath_descriptors

    methods = [mint_method(mid, method_by_id(mid).parameters()) for mid in method_ids]
    roots = [item for item in items if item.isPartOf is None]
    harvest_record = record_harvest(None, None, __version__, root, methods=methods, roots=roots)

    tmp_output = output_path.with_name(output_path.name + ".tmp")
    try:
        combine_descriptors(items, tmp_output, "turtle", descriptors, harvest_record, methods)
    except Exception:
        tmp_output.unlink(missing_ok=True)
        raise
    os.replace(tmp_output, output_path)
