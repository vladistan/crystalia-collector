# LinkML RDF import paths:
#   - SchemaView:         linkml_runtime (public PyPI)
#   - PydanticRDFDumper:  crystalia_collector._vendor.pydantic_rdf_dumper
#   - PydanticRDFLoader:  crystalia_collector._vendor.pydantic_rdf_loader
# PydanticRDFDumper/PydanticRDFLoader are vendored because they exist only in the
# LinkML monorepo fork, not in public PyPI `linkml-runtime` (see
# _vendor/VENDORED.md for provenance and the upstreaming TODO). SchemaView and the
# vendored classes' base classes are all provided by public `linkml-runtime`.
from collections.abc import Iterable
from functools import lru_cache
from importlib.resources import as_file, files
from typing import Any

from linkml_runtime import SchemaView
from pydantic import BaseModel
from rdflib import Graph

from crystalia_collector._vendor.pydantic_rdf_dumper import PydanticRDFDumper
from crystalia_collector._vendor.pydantic_rdf_loader import PydanticRDFLoader
from crystalia_data_model.datamodel.linkml_crystalia import Thing


@lru_cache
def get_schema() -> SchemaView:
    schema_resource = files("crystalia_data_model.schema").joinpath("linkml_crystalia.yaml")
    with as_file(schema_resource) as schema_file:
        return SchemaView(schema=schema_file)


@lru_cache
def _pairs_loader() -> PydanticRDFLoader:
    """Singleton loader for dict_from_pairs.

    dict_from_pairs's per-type_class speedups (field-resolution map, prefixes,
    type-introspection results) are cached on the loader instance, not globally --
    a fresh PydanticRDFLoader() per call would rebuild that cache from scratch
    every time and lose the whole point of the optimization.
    """
    return PydanticRDFLoader()


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


def dict_from_subject(
    rdf: Graph,
    type_class: type[Thing],
    subject: str,
) -> dict[str, Any]:
    """Bulk-extraction counterpart to model_from_rdf: returns the subject's fields as
    a plain dict (CURIE strings for id-reference slots) without building a full
    Pydantic model instance. Use when pulling many subjects' field values out of a
    graph and the cost/side effects of a full model_from_rdf per subject aren't
    needed.
    """
    expanded_subject = get_schema().expand_curie(subject)
    return PydanticRDFLoader().dict_from_subject_triples(  # type: ignore[no-any-return]
        graph=rdf,
        subject=expanded_subject,
        target_class=type_class,
    )


def dict_from_pairs(
    type_class: type[Thing],
    subject: str,
    pairs: Iterable[tuple[str, str | tuple[str, str | None, str | None]]],
) -> dict[str, Any]:
    """Graph-free counterpart to dict_from_subject: same field mapping, literal
    coercion, and list-handling, but takes one subject's (predicate_iri, object)
    pairs directly instead of an rdflib Graph. Use when the caller already has
    per-subject triples from a non-rdflib store (e.g. pyoxigraph) and has no graph
    to hand the loader. A literal object is a (lexical, datatype, lang) tuple, not
    an rdflib Literal -- the caller never constructs one.
    """
    expanded_subject = get_schema().expand_curie(subject)
    return _pairs_loader().dict_from_pairs(  # type: ignore[no-any-return]
        target_class=type_class,
        subject=expanded_subject,
        pairs=pairs,
    )
