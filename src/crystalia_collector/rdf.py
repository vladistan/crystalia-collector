from typing import Type
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import RDFLibDumper
from linkml_runtime.loaders import RDFLibLoader
from pydantic import BaseModel
from rdflib import Graph, URIRef

from functools import lru_cache
from pathlib import Path


from crystalia.datamodel.crystalia import Thing


SCHEMA_DIR = Path(__file__).parent / "data" / "linkml"


@lru_cache
def get_schema() -> SchemaView:
    schema_file = SCHEMA_DIR / "crystalia.yaml"
    return SchemaView(schema=schema_file)


def rdf_from_model(thing: Thing) -> Graph:
    return RDFLibDumper().as_rdf_graph(thing, get_schema())


def model_from_rdf(
    rdf: Graph,
    type_class: Type[Thing],
    subject: str = None,
) -> BaseModel:
    schema = get_schema()
    if subject:
        old_rdf = rdf
        rdf = Graph()
        triples = old_rdf.triples((URIRef(schema.expand_curie(subject)), None, None))
        rdf += triples

    return RDFLibLoader().load(
        source=rdf,
        fmt="turtle",
        target_class=type_class,
        ignore_unmapped_predicates=True,
        schemaview=schema,
    )
