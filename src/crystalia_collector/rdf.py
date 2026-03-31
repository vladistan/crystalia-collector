from functools import lru_cache
from pathlib import Path

# Import spike result (Phase 1):
# - ``linkml`` package is NOT installed; SchemaView, RDFLibDumper, RDFLibLoader
#   remain available from ``linkml_runtime``.
# - Pydantic model classes are available from ``crystalia_data_model.datamodel.linkml_crystalia``
#   and will replace the vendored dataclasses in Phase 3.
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import RDFLibDumper
from linkml_runtime.loaders import RDFLibLoader
from pydantic import BaseModel
from rdflib import Graph, URIRef

from crystalia_collector.data.linkml.crystalia import Thing

SCHEMA_DIR = Path(__file__).parent / "schema"


@lru_cache
def get_schema() -> SchemaView:
    schema_file = SCHEMA_DIR / "crystalia.yaml"
    return SchemaView(schema=schema_file)


def rdf_from_model(thing: Thing) -> Graph:
    return RDFLibDumper().as_rdf_graph(thing, get_schema())  # type: ignore[no-any-return]


def model_from_rdf(
    rdf: Graph,
    type_class: type[Thing],
    subject: str | None = None,
) -> BaseModel:
    schema = get_schema()
    if subject:
        old_rdf = rdf
        rdf = Graph()
        triples = old_rdf.triples((URIRef(schema.expand_curie(subject)), None, None))
        rdf += triples

    return RDFLibLoader().load(  # type: ignore[no-any-return]
        source=rdf,
        fmt="turtle",
        target_class=type_class,
        ignore_unmapped_predicates=True,
        schemaview=schema,
    )
