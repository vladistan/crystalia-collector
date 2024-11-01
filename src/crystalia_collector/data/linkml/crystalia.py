# Auto generated from crystalia.yaml by pythongen.py version: 0.0.1
# Generation date: 2024-10-25T20:07:58
# Schema: crystalia-datamodel
#
# id: https://crystalia.link/ontology
# description: Data model for the Crystalia dataset annotation model
# license: MIT

import dataclasses
from typing import Optional, List, Union, Dict, ClassVar, Any
from dataclasses import dataclass
from linkml_runtime.linkml_model.meta import EnumDefinition, PermissibleValue

from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.metamodelcore import empty_list
from linkml_runtime.utils.yamlutils import YAMLRoot
from linkml_runtime.utils.dataclass_extensions_376 import (
    dataclasses_init_fn_with_kwargs,
)
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from rdflib import URIRef
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.metamodelcore import URIorCURIE

metamodel_version = "1.7.0"
version = None

# Overwrite dataclasses _init_fn to add **kwargs in __init__
dataclasses._init_fn = dataclasses_init_fn_with_kwargs

# Namespaces
CRYD = CurieNamespace("cryd", "https://crystalia.link/data/")
CRYS = CurieNamespace("crys", "https://crystalia.link/ontology/1.0/")
DCMI = CurieNamespace("dcmi", "http://purl.org/dc/dcmitype/")
DCT = CurieNamespace("dct", "http://purl.org/dc/terms/")
LINKML = CurieNamespace("linkml", "https://w3id.org/linkml/")
QUDT = CurieNamespace("qudt", "http://qudt.org/schema/qudt/")
RDF = CurieNamespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = CurieNamespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
UNIT = CurieNamespace("unit", "http://qudt.org/vocab/unit/")
XML = CurieNamespace("xml", "http://www.w3.org/XML/1998/namespace")
XSD = CurieNamespace("xsd", "http://www.w3.org/2001/XMLSchema#")
DEFAULT_ = CRYS


# Types


# Class references
class ThingId(URIorCURIE):
    pass


class DescribableThingId(ThingId):
    pass


class ItemId(DescribableThingId):
    pass


class DescriptorId(DescribableThingId):
    pass


class DescriptorTypeId(ThingId):
    pass


class MethodId(ThingId):
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
class DescribableThing(Thing):
    """
    An item that can be described by one or more descriptors. Could be an item(file) or another descriptor
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["DescribableThing"]
    class_class_curie: ClassVar[str] = "crys:DescribableThing"
    class_name: ClassVar[str] = "DescribableThing"
    class_model_uri: ClassVar[URIRef] = CRYS.DescribableThing

    id: Union[str, DescribableThingId] = None
    hasDescriptor: Optional[
        Union[Union[str, DescriptorId], List[Union[str, DescriptorId]]]
    ] = empty_list()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DescribableThingId):
            self.id = DescribableThingId(self.id)

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
class Item(DescribableThing):
    """
    An individual item for example a file
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Item"]
    class_class_curie: ClassVar[str] = "crys:Item"
    class_name: ClassVar[str] = "Item"
    class_model_uri: ClassVar[URIRef] = CRYS.Item

    id: Union[str, ItemId] = None
    label: str = None
    isPartOf: Union[str, URIorCURIE] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ItemId):
            self.id = ItemId(self.id)

        if self._is_empty(self.label):
            self.MissingRequiredField("label")
        if not isinstance(self.label, str):
            self.label = str(self.label)

        if self._is_empty(self.isPartOf):
            self.MissingRequiredField("isPartOf")
        if not isinstance(self.isPartOf, URIorCURIE):
            self.isPartOf = URIorCURIE(self.isPartOf)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Descriptor(DescribableThing):
    """
    A descriptor for the whole or part of an item or another descriptor
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Descriptor"]
    class_class_curie: ClassVar[str] = "crys:Descriptor"
    class_name: ClassVar[str] = "Descriptor"
    class_model_uri: ClassVar[URIRef] = CRYS.Descriptor

    id: Union[str, DescriptorId] = None
    hasType: Union[str, DescriptorTypeId] = None
    value: str = None
    offset: int = None
    coverage: float = None
    length: Optional[int] = None
    label: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DescriptorId):
            self.id = DescriptorId(self.id)

        if self._is_empty(self.hasType):
            self.MissingRequiredField("hasType")
        if not isinstance(self.hasType, DescriptorTypeId):
            self.hasType = DescriptorTypeId(self.hasType)

        if self._is_empty(self.value):
            self.MissingRequiredField("value")
        if not isinstance(self.value, str):
            self.value = str(self.value)

        if self._is_empty(self.offset):
            self.MissingRequiredField("offset")
        if not isinstance(self.offset, int):
            self.offset = int(self.offset)

        if self._is_empty(self.coverage):
            self.MissingRequiredField("coverage")
        if not isinstance(self.coverage, float):
            self.coverage = float(self.coverage)

        if self.length is not None and not isinstance(self.length, int):
            self.length = int(self.length)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DescriptorType(Thing):
    """
    Details about a descriptor type
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["DescriptorType"]
    class_class_curie: ClassVar[str] = "crys:DescriptorType"
    class_name: ClassVar[str] = "DescriptorType"
    class_model_uri: ClassVar[URIRef] = CRYS.DescriptorType

    id: Union[str, DescriptorTypeId] = None
    label: str = None
    usesMethod: Union[str, MethodId] = None
    max_block_size: Optional[int] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DescriptorTypeId):
            self.id = DescriptorTypeId(self.id)

        if self._is_empty(self.label):
            self.MissingRequiredField("label")
        if not isinstance(self.label, str):
            self.label = str(self.label)

        if self._is_empty(self.usesMethod):
            self.MissingRequiredField("usesMethod")
        if not isinstance(self.usesMethod, MethodId):
            self.usesMethod = MethodId(self.usesMethod)

        if self.max_block_size is not None and not isinstance(self.max_block_size, int):
            self.max_block_size = int(self.max_block_size)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Method(Thing):
    """
    A method used to generate a descriptor
    """

    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = CRYS["Method"]
    class_class_curie: ClassVar[str] = "crys:Method"
    class_name: ClassVar[str] = "Method"
    class_model_uri: ClassVar[URIRef] = CRYS.Method

    id: Union[str, MethodId] = None
    label: str = None
    robustness: Union[str, "DescriptorRobustness"] = None
    comment: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, MethodId):
            self.id = MethodId(self.id)

        if self._is_empty(self.label):
            self.MissingRequiredField("label")
        if not isinstance(self.label, str):
            self.label = str(self.label)

        if self._is_empty(self.robustness):
            self.MissingRequiredField("robustness")
        if not isinstance(self.robustness, DescriptorRobustness):
            self.robustness = DescriptorRobustness(self.robustness)

        if self.comment is not None and not isinstance(self.comment, str):
            self.comment = str(self.comment)

        super().__post_init__(**kwargs)


# Enumerations
class DescriptorRobustness(EnumDefinitionImpl):
    """
    Degree of resilience of the descriptor to changes in the item
    """

    EXTREMELY_HIGH = PermissibleValue(
        text="EXTREMELY_HIGH",
        description="Descriptor is extremely resilient to changes (e.g., SHA512 sum)",
    )
    VERY_HIGH = PermissibleValue(
        text="VERY_HIGH",
        description="Descriptor is very resilient to changes (e.g., MD5 sum)",
    )
    HIGH = PermissibleValue(
        text="HIGH",
        description="Descriptor is highly resilient to changes (e.g., Farmhash, Jenkins hash)",
    )
    MODERATE = PermissibleValue(
        text="MODERATE",
        description="Descriptor is moderately resilient to changes (e.g., CRC sum)",
    )
    LOW = PermissibleValue(
        text="LOW",
        description="Descriptor has low resilience to changes (e.g., length + date + name together)",
    )
    VERY_LOW = PermissibleValue(
        text="VERY_LOW",
        description="Descriptor has very low resilience to changes (e.g., length, date or name individually)",
    )

    _defn = EnumDefinition(
        name="DescriptorRobustness",
        description="Degree of resilience of the descriptor to changes in the item",
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

slots.label = Slot(
    uri=RDFS.label,
    name="label",
    curie=RDFS.curie("label"),
    model_uri=CRYS.label,
    domain=None,
    range=str,
)

slots.comment = Slot(
    uri=RDFS.comment,
    name="comment",
    curie=RDFS.curie("comment"),
    model_uri=CRYS.comment,
    domain=None,
    range=Optional[str],
)

slots.isPartOf = Slot(
    uri=DCT.isPartOf,
    name="isPartOf",
    curie=DCT.curie("isPartOf"),
    model_uri=CRYS.isPartOf,
    domain=None,
    range=Union[str, URIorCURIE],
)

slots.hasDescriptor = Slot(
    uri=CRYS.hasDescriptor,
    name="hasDescriptor",
    curie=CRYS.curie("hasDescriptor"),
    model_uri=CRYS.hasDescriptor,
    domain=None,
    range=Optional[Union[Union[str, DescriptorId], List[Union[str, DescriptorId]]]],
)

slots.max_block_size = Slot(
    uri=CRYS.max_block_size,
    name="max_block_size",
    curie=CRYS.curie("max_block_size"),
    model_uri=CRYS.max_block_size,
    domain=None,
    range=Optional[int],
)

slots.hasType = Slot(
    uri=CRYS.hasType,
    name="hasType",
    curie=CRYS.curie("hasType"),
    model_uri=CRYS.hasType,
    domain=None,
    range=Union[str, DescriptorTypeId],
)

slots.value = Slot(
    uri=CRYS.value,
    name="value",
    curie=CRYS.curie("value"),
    model_uri=CRYS.value,
    domain=None,
    range=str,
)

slots.offset = Slot(
    uri=CRYS.offset,
    name="offset",
    curie=CRYS.curie("offset"),
    model_uri=CRYS.offset,
    domain=None,
    range=int,
)

slots.length = Slot(
    uri=CRYS.length,
    name="length",
    curie=CRYS.curie("length"),
    model_uri=CRYS.length,
    domain=None,
    range=Optional[int],
)

slots.robustness = Slot(
    uri=CRYS.robustness,
    name="robustness",
    curie=CRYS.curie("robustness"),
    model_uri=CRYS.robustness,
    domain=None,
    range=Union[str, "DescriptorRobustness"],
)

slots.coverage = Slot(
    uri=CRYS.coverage,
    name="coverage",
    curie=CRYS.curie("coverage"),
    model_uri=CRYS.coverage,
    domain=None,
    range=float,
)

slots.usesMethod = Slot(
    uri=CRYS.usesMethod,
    name="usesMethod",
    curie=CRYS.curie("usesMethod"),
    model_uri=CRYS.usesMethod,
    domain=None,
    range=Union[str, MethodId],
)

slots.descriptor__label = Slot(
    uri=RDFS.label,
    name="descriptor__label",
    curie=RDFS.curie("label"),
    model_uri=CRYS.descriptor__label,
    domain=None,
    range=Optional[str],
)
