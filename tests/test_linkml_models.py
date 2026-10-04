import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from crystalia_collector.rdf import dict_from_pairs, dict_from_subject, model_from_rdf, rdf_from_model
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor, HarvestRecord, Item, Method


@pytest.fixture
def item():
    return Item(
        id="s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202-samples-cohort/a.txt",
        isPartOf="https://registry.opendata.aws/ilmn-dragen-1kgp",
        label="Short file in the cohort",
    )


@pytest.fixture
def method_sha256():
    return Method(
        id="cryd:sha256",
        label="SHA256",
    )


@pytest.fixture
def descriptor_short_file_full_hash(method_sha256):
    descriptor = Descriptor(
        id="cryd:desc/bob.txt/sha256_whole_file/1",
        hasType="cryd:sha256_whole_file",
        value="02342342aaa223",
        length=4096,
    )

    return descriptor


def test_create_item(item):
    """Create a descriptor."""

    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"


def test_descriptor_model(item, descriptor_short_file_full_hash):
    item.hasDescriptor = [descriptor_short_file_full_hash.id]
    descriptor_short_file_full_hash.hasDescriptor = [descriptor_short_file_full_hash.id]


def test_rdf_from_model(
    item,
    method_sha256,
    descriptor_short_file_full_hash,
):
    item.hasDescriptor = [descriptor_short_file_full_hash.id]
    item_rdf = rdf_from_model(item)
    method_rdf = rdf_from_model(method_sha256)
    descriptor_rdf = rdf_from_model(descriptor_short_file_full_hash)

    g = item_rdf + method_rdf + descriptor_rdf

    g.serialize(destination="test.ttl", format="ttl")


def test_model_from_rdf(short_file_single_descriptor):
    rdf_graph = Graph()
    rdf_graph.parse(short_file_single_descriptor, format="turtle")

    item_uri = "s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202/samples-cohort/a.txt"

    # Use the function to get the data class instance
    item = model_from_rdf(rdf_graph, Item, subject=item_uri)

    # Perform assertions
    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"

    assert len(item.hasDescriptor) == 1

    descriptor = model_from_rdf(rdf_graph, Descriptor, subject=item.hasDescriptor[0])
    # The fixture pins the old cryd: base URI (https://crystalia.link/data/); the
    # loader cannot recompact it to cryd: under the current schema's prefix map
    # (which now resolves cryd: under w3id.org), so it returns the full IRI.
    assert descriptor.hasType == "https://crystalia.link/data/sha256_whole_file"

    method = model_from_rdf(rdf_graph, Method, subject="https://crystalia.link/data/sha256")
    assert method.label == "SHA256"


def test_dict_from_subject_matches_model_from_rdf_fields(short_file_single_descriptor):
    """dict_from_subject is the bulk-extraction counterpart to model_from_rdf: same
    field resolution and value conversion, returned as a plain dict instead of a
    validated model instance (no model instantiation/shell/cache machinery).
    """
    rdf_graph = Graph()
    rdf_graph.parse(short_file_single_descriptor, format="turtle")

    item_uri = "s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202/samples-cohort/a.txt"

    item_model = model_from_rdf(rdf_graph, Item, subject=item_uri)
    item_dict = dict_from_subject(rdf_graph, Item, subject=item_uri)

    assert item_dict["label"] == item_model.label == "Short file in the cohort"
    assert item_dict["isPartOf"] == item_model.isPartOf
    assert item_dict["hasDescriptor"] == item_model.hasDescriptor


def test_dict_from_subject_does_not_instantiate_a_model(short_file_single_descriptor):
    rdf_graph = Graph()
    rdf_graph.parse(short_file_single_descriptor, format="turtle")

    item_uri = "s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202/samples-cohort/a.txt"

    result = dict_from_subject(rdf_graph, Item, subject=item_uri)

    assert isinstance(result, dict)
    assert not isinstance(result, Item)


def test_dict_from_pairs_matches_dict_from_subject(short_file_single_descriptor):
    """dict_from_pairs is the graph-free counterpart to dict_from_subject: same
    field mapping/literal coercion/list handling, driven by (predicate, object)
    pairs instead of an rdflib Graph lookup (for callers with no Graph on hand,
    e.g. a pyoxigraph-backed loader).
    """
    rdf_graph = Graph()
    rdf_graph.parse(short_file_single_descriptor, format="turtle")

    item_uri = "s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202/samples-cohort/a.txt"
    item_dict = dict_from_subject(rdf_graph, Item, subject=item_uri)

    pairs: list[tuple[str, str | Literal]] = [
        (str(p), o if isinstance(o, Literal) else str(o))
        for p, o in rdf_graph.predicate_objects(URIRef(item_uri))
        if str(p) != str(RDF.type)
    ]
    pairs_dict = dict_from_pairs(Item, subject=item_uri, pairs=pairs)

    assert pairs_dict["label"] == item_dict["label"] == "Short file in the cohort"
    assert pairs_dict["isPartOf"] == item_dict["isPartOf"]
    assert pairs_dict["hasDescriptor"] == item_dict["hasDescriptor"]


def test_dict_from_pairs_coerces_literal_datatypes():
    descriptor = Descriptor(id="cryd:d1", hasType="crys:dtype/file-size", value="4", length=4096)
    g = rdf_from_model(descriptor)
    subject = "https://w3id.org/crystalia/data/d1"
    pairs: list[tuple[str, str | Literal]] = [
        (str(p), o if isinstance(o, Literal) else str(o))
        for p, o in g.predicate_objects(URIRef(subject))
        if str(p) != str(RDF.type)
    ]

    result = dict_from_pairs(Descriptor, subject=subject, pairs=pairs)

    assert result["value"] == "4"
    assert result["length"] == 4096


def test_dict_from_pairs_iri_object_becomes_curie():
    subject = "cryd:top1"
    pairs = [("https://w3id.org/crystalia/hasType", "https://w3id.org/crystalia/dtype/glimpse")]

    result = dict_from_pairs(Descriptor, subject=subject, pairs=pairs)

    assert result["hasType"] == "crys:dtype/glimpse"


def test_dict_from_pairs_literal_object():
    subject = "cryd:top1"
    pairs = [("https://w3id.org/crystalia/value", Literal("abc123"))]

    result = dict_from_pairs(Descriptor, subject=subject, pairs=pairs)

    assert result["value"] == "abc123"


def test_model_from_rdf_without_subject_resolves_item_by_type(test_dir):
    """Regression: loading without an explicit subject must resolve the Item by
    rdf:type rather than falling back to an arbitrary (wrong) subject.

    The fixture declares Method, DescriptorType and Descriptor before the Item,
    all using the slash-convention crys: type URIs. Without the class_uri fix the
    loader searches for a hash-separated type URI absent from the graph, fails to
    match, and falls back to the first arbitrary subject -- mis-validating a
    Method/Descriptor as an Item (wrong label or a missing-field ValidationError).
    This is the no-explicit-subject path that the `combine` command exercises.
    """
    rdf_graph = Graph()
    rdf_graph.parse(test_dir / "rdf_data" / "multi_subject_no_root.ttl", format="turtle")

    item = model_from_rdf(rdf_graph, Item)

    assert isinstance(item, Item)
    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"
    assert str(item.id).endswith("samples-cohort/a.txt")


def test_dumper_emits_uriref_for_id_reference_slots():
    """hasDescriptor, isPartOf, hasType, hasRoot and usesMethod hold another
    entity's id, not inline data -- they must round-trip as URIRefs, not
    xsd:string literals (write-side asymmetry: the loader already treats them
    as references, per Phase 2/3's ensure_valid(resolve=...) self-checks against
    real loaded output).
    """
    child = Descriptor(id="cryd:child1", hasType="crys:dtype/filename", value="a.txt")
    top = Descriptor(
        id="cryd:top1",
        hasType="crys:dtype/glimpse",
        value="v0:deadbeef",
        hasDescriptor=[child.id],
    )
    method = Method(id="cryd:method/m1", label="glimpse")
    root_item = Item(id="crys:root1", label="root", isPartOf=None)
    child_item = Item(id="crys:child-item1", label="child", isPartOf=root_item.id, hasDescriptor=[top.id])
    harvest = HarvestRecord(id="cryd:harvest/h1", usesMethod=[method.id], hasRoot=[root_item.id])

    g = rdf_from_model(top) + rdf_from_model(child) + rdf_from_model(method)
    g += rdf_from_model(root_item) + rdf_from_model(child_item) + rdf_from_model(harvest)

    cryd = "https://w3id.org/crystalia/data/"
    crys = "https://w3id.org/crystalia/"
    checks = [
        (URIRef(f"{cryd}top1"), URIRef(f"{crys}hasDescriptor"), URIRef(f"{cryd}child1")),
        (URIRef(f"{crys}child-item1"), URIRef("http://purl.org/dc/terms/isPartOf"), URIRef(f"{crys}root1")),
        (URIRef(f"{cryd}harvest/h1"), URIRef(f"{crys}hasRoot"), URIRef(f"{crys}root1")),
        (URIRef(f"{cryd}harvest/h1"), URIRef(f"{crys}usesMethod"), URIRef(f"{cryd}method/m1")),
    ]
    for subj, pred, expected_obj in checks:
        objs = list(g.objects(subj, pred))
        assert len(objs) == 1, f"expected exactly one {pred} triple from {subj}"
        assert isinstance(objs[0], URIRef), f"{pred} from {subj} emitted {type(objs[0])}, not URIRef"
        assert objs[0] == expected_obj

    hastype_objs = list(g.objects(URIRef(f"{cryd}top1"), URIRef(f"{crys}hasType")))
    assert len(hastype_objs) == 1
    assert isinstance(hastype_objs[0], URIRef)
