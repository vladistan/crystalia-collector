from functools import lru_cache
from pathlib import Path

from crystalia_data_model.datamodel.linkml_crystalia import Thing
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.pydantic_rdf_dumper import PydanticRDFDumper
from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader
from pydantic import BaseModel
from rdflib import Graph, Literal, URIRef

SCHEMA_DIR = Path(__file__).parent / "schema"

# Predicates whose string values should be expanded to URI references
_URI_PREDICATES = frozenset(
    {
        URIRef("https://w3id.org/crystalia/hasDescriptor"),
        URIRef("https://w3id.org/crystalia/hasType"),
        URIRef("http://purl.org/dc/terms/isPartOf"),
    },
)


@lru_cache
def get_schema() -> SchemaView:
    schema_file = SCHEMA_DIR / "crystalia.yaml"
    return SchemaView(schema=schema_file)


def _expand_curie(value: str, prefixes: dict[str, str]) -> URIRef:
    """Expand a CURIE string like 'cryd:abc' to a full URIRef."""
    if ":" in value:
        prefix, local = value.split(":", 1)
        if prefix in prefixes:
            return URIRef(f"{prefixes[prefix]}{local}")
    return URIRef(value)


def _rewrite_curie_literals(g: Graph) -> Graph:
    """Replace string literals with URI references for known predicates."""
    prefixes = {str(p): str(ns) for p, ns in g.namespaces()}
    removals: list[tuple[URIRef, URIRef, Literal]] = []
    additions: list[tuple[URIRef, URIRef, URIRef]] = []
    for s, p, o in g:
        if isinstance(s, URIRef) and isinstance(p, URIRef) and p in _URI_PREDICATES and isinstance(o, Literal):
            value = str(o)
            if ":" in value:
                removals.append((s, p, o))
                additions.append((s, p, _expand_curie(value, prefixes)))
    for old in removals:
        g.remove(old)
    for new in additions:
        g.add(new)
    return g


def rdf_from_model(thing: Thing) -> Graph:
    g = PydanticRDFDumper().as_rdf_graph(thing)
    return _rewrite_curie_literals(g)


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
