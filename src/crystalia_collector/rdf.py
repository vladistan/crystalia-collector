# LinkML RDF import paths:
#   - SchemaView:         linkml_runtime (public PyPI)
#   - PydanticRDFDumper:  crystalia_collector._vendor.pydantic_rdf_dumper
#   - PydanticRDFLoader:  crystalia_collector._vendor.pydantic_rdf_loader
# PydanticRDFDumper/PydanticRDFLoader are vendored because they exist only in the
# LinkML monorepo fork, not in public PyPI `linkml-runtime` (see
# _vendor/VENDORED.md for provenance and the upstreaming TODO). SchemaView and the
# vendored classes' base classes are all provided by public `linkml-runtime`.
from functools import lru_cache
from pathlib import Path

from linkml_runtime import SchemaView
from pydantic import BaseModel
from rdflib import Graph

from crystalia_collector._vendor.pydantic_rdf_dumper import PydanticRDFDumper
from crystalia_collector._vendor.pydantic_rdf_loader import PydanticRDFLoader
from crystalia_data_model.datamodel.linkml_crystalia import Thing

SCHEMA_DIR = Path(__file__).parent / "schema"


@lru_cache
def get_schema() -> SchemaView:
    schema_file = SCHEMA_DIR / "crystalia.yaml"
    return SchemaView(schema=schema_file)


def rdf_from_model(thing: Thing) -> Graph:
    return PydanticRDFDumper().as_rdf_graph(thing)  # type: ignore[no-any-return]


def model_from_rdf(
    rdf: Graph,
    type_class: type[Thing],
    subject: str | None = None,
) -> BaseModel:
    root_subject: str | None = None
    if subject:
        root_subject = get_schema().expand_curie(subject)

    return PydanticRDFLoader().load(  # type: ignore[no-any-return]
        source=rdf,
        fmt="turtle",
        target_class=type_class,
        root_subject=root_subject,
    )
