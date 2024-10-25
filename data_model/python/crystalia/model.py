from __future__ import annotations 

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal 
from enum import Enum 
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator
)


metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )
    pass




class LinkMLMeta(RootModel):
    root: Dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'crys',
     'default_range': 'string',
     'description': 'Data model for the Crystalia dataset annotation model',
     'id': 'https://crystalia.link/ontology',
     'imports': ['linkml:types'],
     'license': 'MIT',
     'name': 'crystalia-datamodel',
     'prefixes': {'crys': {'prefix_prefix': 'crys',
                           'prefix_reference': 'https://crystalia.link/ontology/1.0/'},
                  'dcmi': {'prefix_prefix': 'dcmi',
                           'prefix_reference': 'http://purl.org/dc/dcmitype/'},
                  'dct': {'prefix_prefix': 'dct',
                          'prefix_reference': 'http://purl.org/dc/terms/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'qudt': {'prefix_prefix': 'qudt',
                           'prefix_reference': 'http://qudt.org/schema/qudt/'},
                  'rdf': {'prefix_prefix': 'rdf',
                          'prefix_reference': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'},
                  'rdfs': {'prefix_prefix': 'rdfs',
                           'prefix_reference': 'http://www.w3.org/2000/01/rdf-schema#'},
                  'unit': {'prefix_prefix': 'unit',
                           'prefix_reference': 'http://qudt.org/vocab/unit/'},
                  'xml': {'prefix_prefix': 'xml',
                          'prefix_reference': 'http://www.w3.org/XML/1998/namespace'},
                  'xsd': {'prefix_prefix': 'xsd',
                          'prefix_reference': 'http://www.w3.org/2001/XMLSchema#'}},
     'see_also': ['https://vladistan.github.com/crystalia-collector'],
     'source_file': 'schema/crystalia.yaml',
     'title': 'Crystalia Data Model'} )

class DescriptorRobustness(str, Enum):
    """
    Degree of resilience of the descriptor to changes in the item
    """
    # Descriptor is extremely resilient to changes (e.g., SHA512 sum)
    EXTREMELY_HIGH = "EXTREMELY_HIGH"
    # Descriptor is very resilient to changes (e.g., MD5 sum)
    VERY_HIGH = "VERY_HIGH"
    # Descriptor is highly resilient to changes (e.g., Farmhash, Jenkins hash)
    HIGH = "HIGH"
    # Descriptor is moderately resilient to changes (e.g., CRC sum)
    MODERATE = "MODERATE"
    # Descriptor has low resilience to changes (e.g., length + date + name together)
    LOW = "LOW"
    # Descriptor has very low resilience to changes (e.g., length, date or name individually)
    VERY_LOW = "VERY_LOW"



class Thing(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://crystalia.link/ontology'})

    id: str = Field(..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['Thing']} })


class DescribableThing(Thing):
    """
    An item that can be described by one or more descriptors. Could be an item(file) or another descriptor
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://crystalia.link/ontology'})

    hasDescriptor: Optional[List[str]] = Field(None, description="""The descriptors associated with an item""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor', 'domain_of': ['DescribableThing']} })
    id: str = Field(..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['Thing']} })


class Item(DescribableThing):
    """
    An individual item for example a file
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://crystalia.link/ontology'})

    label: str = Field(..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'slot_uri': 'rdfs:label'} })
    isPartOf: str = Field(..., description="""The items in the dataset such as files""", json_schema_extra = { "linkml_meta": {'alias': 'isPartOf', 'domain_of': ['Item'], 'slot_uri': 'dct:isPartOf'} })
    hasDescriptor: Optional[List[str]] = Field(None, description="""The descriptors associated with an item""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor', 'domain_of': ['DescribableThing']} })
    id: str = Field(..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['Thing']} })


class Descriptor(DescribableThing):
    """
    A descriptor for the whole or part of an item or another descriptor
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://crystalia.link/ontology'})

    hasType: str = Field(..., description="""The type of the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'hasType', 'domain_of': ['Descriptor']} })
    value: str = Field(..., description="""The value of the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'value', 'domain_of': ['Descriptor']} })
    offset: int = Field(..., description="""The starting offset for partial file descriptors""", json_schema_extra = { "linkml_meta": {'alias': 'offset', 'domain_of': ['Descriptor'], 'unit': {'ucum_code': 'byte'}} })
    length: Optional[int] = Field(None, description="""The length of the data described by the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'length', 'domain_of': ['Descriptor'], 'unit': {'ucum_code': 'byte'}} })
    coverage: float = Field(..., description="""The coverage of the descriptor (0.0 to 1.0)""", json_schema_extra = { "linkml_meta": {'alias': 'coverage', 'domain_of': ['Descriptor']} })
    label: Optional[str] = Field(None, description="""A human-readable label""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'slot_uri': 'rdfs:label'} })
    hasDescriptor: Optional[List[str]] = Field(None, description="""The descriptors associated with an item""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor', 'domain_of': ['DescribableThing']} })
    id: str = Field(..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['Thing']} })


class DescriptorType(Thing):
    """
    Details about a descriptor type
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://crystalia.link/ontology'})

    label: str = Field(..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'slot_uri': 'rdfs:label'} })
    usesMethod: str = Field(..., description="""The method used to generate the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'usesMethod', 'domain_of': ['DescriptorType']} })
    max_block_size: Optional[int] = Field(None, description="""The maximum size of the block of data described by the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'max_block_size', 'domain_of': ['DescriptorType']} })
    id: str = Field(..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['Thing']} })


class Method(Thing):
    """
    A method used to generate a descriptor
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://crystalia.link/ontology'})

    label: str = Field(..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'slot_uri': 'rdfs:label'} })
    comment: Optional[str] = Field(None, description="""A description of the item""", json_schema_extra = { "linkml_meta": {'alias': 'comment', 'domain_of': ['Method'], 'slot_uri': 'rdfs:comment'} })
    robustness: DescriptorRobustness = Field(..., description="""The robustness category of the descriptor type""", json_schema_extra = { "linkml_meta": {'alias': 'robustness', 'domain_of': ['Method']} })
    id: str = Field(..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['Thing']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Thing.model_rebuild()
DescribableThing.model_rebuild()
Item.model_rebuild()
Descriptor.model_rebuild()
DescriptorType.model_rebuild()
Method.model_rebuild()

