# Auto generated from linkml_crystalia.yaml by pythongen.py version: 0.0.1
# Generation date: 2024-10-24T07:09:27
# Schema: linkml-crystalia
#
# id: https://crystalia.v-lad.org/ontology
# description: Ontology for the Crystalia dataset annotation model
# license: MIT

import dataclasses
from typing import Optional, List, Union, Dict, ClassVar, Any
from dataclasses import dataclass
from linkml_runtime.linkml_model.meta import EnumDefinition, PermissibleValue

from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.metamodelcore import empty_list
from linkml_runtime.utils.yamlutils import YAMLRoot, extended_str
from linkml_runtime.utils.dataclass_extensions_376 import (
    dataclasses_init_fn_with_kwargs,
)
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from rdflib import URIRef
from linkml_runtime.utils.curienamespace import CurieNamespace

metamodel_version = "1.7.0"
version = None

# Overwrite dataclasses _init_fn to add **kwargs in __init__
dataclasses._init_fn = dataclasses_init_fn_with_kwargs

# Namespaces
PATO = CurieNamespace("PATO", "http://purl.obolibrary.org/obo/PATO_")
CRYS = CurieNamespace("crys", "https://w3id.org/crystalia/")
EXAMPLE = CurieNamespace("example", "https://example.org/")
LINKML = CurieNamespace("linkml", "https://w3id.org/linkml/")
OWL = CurieNamespace("owl", "http://www.w3.org/2002/07/owl#")
RDF = CurieNamespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = CurieNamespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
SCHEMA = CurieNamespace("schema", "http://schema.org/")
XML = CurieNamespace("xml", "http://www.w3.org/XML/1998/namespace")
XSD = CurieNamespace("xsd", "http://www.w3.org/2001/XMLSchema#")
DEFAULT_ = CRYS


# Types


# Class references
class ThingId(extended_str):
    pass


class DatasetId(ThingId):
    pass


class DescribableEntityId(ThingId):
    pass


class ItemId(DescribableEntityId):
    pass


class DescriptorId(DescribableEntityId):
    pass


class DescriptorTypeId(ThingId):
    pass


@dataclass(repr=False)
class Thing(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Thing"]
    class_class_curie: ClassVar[str] = "crys:Thing"
    class_name: ClassVar[str] = "Thing"
    class_model_uri: ClassVar[URIRef] = CRYS.Thing

    id: Union[str, ThingId] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ThingId):
            self.id = ThingId(self.id)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Dataset(Thing):
    """
    A collection of items (e.g., files) with associated metadata
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Dataset"]
    class_class_curie: ClassVar[str] = "crys:Dataset"
    class_name: ClassVar[str] = "Dataset"
    class_model_uri: ClassVar[URIRef] = CRYS.Dataset

    id: Union[str, DatasetId] = None
    containsItem: Optional[Union[Union[str, ItemId], List[Union[str, ItemId]]]] = (
        empty_list()
    )

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DatasetId):
            self.id = DatasetId(self.id)

        if not isinstance(self.containsItem, list):
            self.containsItem = (
                [self.containsItem] if self.containsItem is not None else []
            )
        self.containsItem = [
            v if isinstance(v, ItemId) else ItemId(v) for v in self.containsItem
        ]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DescribableEntity(Thing):
    """
    Something that can be described by a descriptop
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["DescribableEntity"]
    class_class_curie: ClassVar[str] = "crys:DescribableEntity"
    class_name: ClassVar[str] = "DescribableEntity"
    class_model_uri: ClassVar[URIRef] = CRYS.DescribableEntity

    id: Union[str, DescribableEntityId] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DescribableEntityId):
            self.id = DescribableEntityId(self.id)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Item(DescribableEntity):
    """
    An individual item (e.g., file) in the dataset
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Item"]
    class_class_curie: ClassVar[str] = "crys:Item"
    class_name: ClassVar[str] = "Item"
    class_model_uri: ClassVar[URIRef] = CRYS.Item

    id: Union[str, ItemId] = None
    hasDescriptor: Optional[
        Union[Union[str, DescriptorId], List[Union[str, DescriptorId]]]
    ] = empty_list()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ItemId):
            self.id = ItemId(self.id)

        if not isinstance(self.hasDescriptor, list):
            self.hasDescriptor = (
                [self.hasDescriptor] if self.hasDescriptor is not None else []
            )
        self.hasDescriptor = [
            v if isinstance(v, DescriptorId) else DescriptorId(v)
            for v in self.hasDescriptor
        ]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Descriptor(DescribableEntity):
    """
    A descriptor for an aspect of an item or another descriptor
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Descriptor"]
    class_class_curie: ClassVar[str] = "crys:Descriptor"
    class_name: ClassVar[str] = "Descriptor"
    class_model_uri: ClassVar[URIRef] = CRYS.Descriptor

    id: Union[str, DescriptorId] = None
    hasType: Optional[str] = None
    hasValue: Optional[str] = None
    hasStartOffset: Optional[int] = None
    hasLength: Optional[int] = None
    describes: Optional[Union[str, ThingId]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DescriptorId):
            self.id = DescriptorId(self.id)

        if self.hasType is not None and not isinstance(self.hasType, str):
            self.hasType = str(self.hasType)

        if self.hasValue is not None and not isinstance(self.hasValue, str):
            self.hasValue = str(self.hasValue)

        if self.hasStartOffset is not None and not isinstance(self.hasStartOffset, int):
            self.hasStartOffset = int(self.hasStartOffset)

        if self.hasLength is not None and not isinstance(self.hasLength, int):
            self.hasLength = int(self.hasLength)

        if self.describes is not None and not isinstance(self.describes, ThingId):
            self.describes = ThingId(self.describes)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DescriptorType(Thing):
    """
    The type of a descriptor, including its quality and coverage
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["DescriptorType"]
    class_class_curie: ClassVar[str] = "crys:DescriptorType"
    class_name: ClassVar[str] = "DescriptorType"
    class_model_uri: ClassVar[URIRef] = CRYS.DescriptorType

    id: Union[str, DescriptorTypeId] = None
    hasName: Optional[str] = None
    hasQuality: Optional[Union[str, "DescriptorQuality"]] = None
    hasCoverage: Optional[float] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DescriptorTypeId):
            self.id = DescriptorTypeId(self.id)

        if self.hasName is not None and not isinstance(self.hasName, str):
            self.hasName = str(self.hasName)

        if self.hasQuality is not None and not isinstance(
            self.hasQuality, DescriptorQuality
        ):
            self.hasQuality = DescriptorQuality(self.hasQuality)

        if self.hasCoverage is not None and not isinstance(self.hasCoverage, float):
            self.hasCoverage = float(self.hasCoverage)

        super().__post_init__(**kwargs)


# Enumerations
class DescriptorQuality(EnumDefinitionImpl):
    EXTREMELY_LOW = PermissibleValue(
        text="EXTREMELY_LOW",
        description="Extremely low quality",
    )
    VERY_LOW = PermissibleValue(
        text="VERY_LOW",
        description="Very low quality",
    )
    LOW = PermissibleValue(
        text="LOW",
        description="Low quality",
    )
    MEDIUM_LOW = PermissibleValue(
        text="MEDIUM_LOW",
        description="Medium-low quality",
    )
    MEDIUM = PermissibleValue(
        text="MEDIUM",
        description="Medium quality",
    )
    MEDIUM_HIGH = PermissibleValue(
        text="MEDIUM_HIGH",
        description="Medium-high quality",
    )
    HIGH = PermissibleValue(
        text="HIGH",
        description="High quality",
    )
    VERY_HIGH = PermissibleValue(
        text="VERY_HIGH",
        description="Very high quality",
    )

    _defn = EnumDefinition(
        name="DescriptorQuality",
    )


# Slots
class slots:
    pass


slots.id = Slot(
    uri=CRYS.id,
    name="id",
    curie=CRYS.curie("id"),
    model_uri=CRYS.id,
    domain=None,
    range=URIRef,
)

slots.containsItem = Slot(
    uri=CRYS.containsItem,
    name="containsItem",
    curie=CRYS.curie("containsItem"),
    model_uri=CRYS.containsItem,
    domain=Dataset,
    range=Optional[Union[Union[str, ItemId], List[Union[str, ItemId]]]],
)

slots.hasDescriptor = Slot(
    uri=CRYS.hasDescriptor,
    name="hasDescriptor",
    curie=CRYS.curie("hasDescriptor"),
    model_uri=CRYS.hasDescriptor,
    domain=None,
    range=Optional[Union[Union[str, DescriptorId], List[Union[str, DescriptorId]]]],
)

slots.hasType = Slot(
    uri=CRYS.hasType,
    name="hasType",
    curie=CRYS.curie("hasType"),
    model_uri=CRYS.hasType,
    domain=None,
    range=Optional[str],
)

slots.hasValue = Slot(
    uri=CRYS.hasValue,
    name="hasValue",
    curie=CRYS.curie("hasValue"),
    model_uri=CRYS.hasValue,
    domain=None,
    range=Optional[str],
)

slots.hasStartOffset = Slot(
    uri=CRYS.hasStartOffset,
    name="hasStartOffset",
    curie=CRYS.curie("hasStartOffset"),
    model_uri=CRYS.hasStartOffset,
    domain=None,
    range=Optional[int],
)

slots.hasLength = Slot(
    uri=CRYS.hasLength,
    name="hasLength",
    curie=CRYS.curie("hasLength"),
    model_uri=CRYS.hasLength,
    domain=None,
    range=Optional[int],
)

slots.hasName = Slot(
    uri=CRYS.hasName,
    name="hasName",
    curie=CRYS.curie("hasName"),
    model_uri=CRYS.hasName,
    domain=None,
    range=Optional[str],
)

slots.hasQuality = Slot(
    uri=CRYS.hasQuality,
    name="hasQuality",
    curie=CRYS.curie("hasQuality"),
    model_uri=CRYS.hasQuality,
    domain=None,
    range=Optional[Union[str, "DescriptorQuality"]],
)

slots.hasCoverage = Slot(
    uri=CRYS.hasCoverage,
    name="hasCoverage",
    curie=CRYS.curie("hasCoverage"),
    model_uri=CRYS.hasCoverage,
    domain=None,
    range=Optional[float],
)

slots.describes = Slot(
    uri=CRYS.describes,
    name="describes",
    curie=CRYS.curie("describes"),
    model_uri=CRYS.describes,
    domain=None,
    range=Optional[Union[str, ThingId]],
)
