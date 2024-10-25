from linkml_runtime import SchemaView
from linkml_runtime.dumpers import RDFLibDumper
from linkml_runtime.loaders import RDFLibLoader
from rdflib import Graph

from functools import lru_cache
from pathlib import Path

from linkml_runtime.utils.curienamespace import CurieNamespace


from crystalia.datamodel.crystalia import Thing



SCHEMA_DIR = Path(__file__).parent / "data" / "linkml"


@lru_cache
def get_schema() -> SchemaView:
    schema_file = SCHEMA_DIR / "crystalia.yaml"
    return SchemaView(schema=schema_file)


def rdf_from_model(thing: Thing) -> Graph:
    


    return RDFLibDumper().as_rdf_graph(thing, get_schema())

