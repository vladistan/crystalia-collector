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
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.7.0"
version = "0.0.1"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'classes': {'DescribableThing': {'class_uri': 'crys:DescribableThing',
                                      'description': 'An item that can be '
                                                     'described by one or more '
                                                     'descriptors. Could be an '
                                                     'item(file) or another '
                                                     'descriptor',
                                      'from_schema': 'https://w3id.org/crystalia',
                                      'is_a': 'Thing',
                                      'name': 'DescribableThing',
                                      'slots': ['hasDescriptor']},
                 'Descriptor': {'attributes': {'label': {'description': 'A '
                                                                        'human-readable '
                                                                        'label',
                                                         'domain_of': ['Item',
                                                                       'Descriptor',
                                                                       'DescriptorType',
                                                                       'Method'],
                                                         'from_schema': 'https://w3id.org/crystalia',
                                                         'name': 'label',
                                                         'required': False,
                                                         'slot_uri': 'rdfs:label'}},
                                'class_uri': 'crys:Descriptor',
                                'description': 'A descriptor for the whole or part '
                                               'of an item or another descriptor',
                                'from_schema': 'https://w3id.org/crystalia',
                                'is_a': 'DescribableThing',
                                'name': 'Descriptor',
                                'slots': ['hasType',
                                          'value',
                                          'offset',
                                          'length',
                                          'coverage']},
                 'DescriptorType': {'class_uri': 'crys:DescriptorType',
                                    'description': 'Details about a descriptor '
                                                   'type',
                                    'from_schema': 'https://w3id.org/crystalia',
                                    'is_a': 'Thing',
                                    'name': 'DescriptorType',
                                    'slots': ['label',
                                              'usesMethod',
                                              'max_block_size']},
                 'Item': {'class_uri': 'crys:Item',
                          'description': 'An individual item for example a file',
                          'from_schema': 'https://w3id.org/crystalia',
                          'is_a': 'DescribableThing',
                          'name': 'Item',
                          'slots': ['label', 'isPartOf']},
                 'Method': {'class_uri': 'crys:Method',
                            'description': 'A method used to generate a descriptor',
                            'from_schema': 'https://w3id.org/crystalia',
                            'is_a': 'Thing',
                            'name': 'Method',
                            'slots': ['label', 'comment', 'robustness']},
                 'Thing': {'class_uri': 'crys:Thing',
                           'description': 'Anything that has an id',
                           'from_schema': 'https://w3id.org/crystalia',
                           'name': 'Thing',
                           'slots': ['id']}},
     'default_prefix': 'crys',
     'default_range': 'string',
     'description': 'Data model for the Crystalia dataset annotation model',
     'enums': {'descriptor_robustness': {'description': 'Degree of resilience of '
                                                        'the descriptor to changes '
                                                        'in the item',
                                         'enum_uri': 'crys:DescriptorRobustness',
                                         'from_schema': 'https://w3id.org/crystalia',
                                         'name': 'descriptor_robustness',
                                         'permissible_values': {'EXTREMELY_HIGH': {'description': 'Descriptor '
                                                                                                  'is '
                                                                                                  'extremely '
                                                                                                  'resilient '
                                                                                                  'to '
                                                                                                  'changes '
                                                                                                  '(e.g., '
                                                                                                  'SHA512 '
                                                                                                  'sum)',
                                                                                   'text': 'EXTREMELY_HIGH'},
                                                                'HIGH': {'description': 'Descriptor '
                                                                                        'is '
                                                                                        'highly '
                                                                                        'resilient '
                                                                                        'to '
                                                                                        'changes '
                                                                                        '(e.g., '
                                                                                        'Farmhash, '
                                                                                        'Jenkins '
                                                                                        'hash)',
                                                                         'text': 'HIGH'},
                                                                'LOW': {'description': 'Descriptor '
                                                                                       'has '
                                                                                       'low '
                                                                                       'resilience '
                                                                                       'to '
                                                                                       'changes '
                                                                                       '(e.g., '
                                                                                       'length '
                                                                                       '+ '
                                                                                       'date '
                                                                                       '+ '
                                                                                       'name '
                                                                                       'together)',
                                                                        'text': 'LOW'},
                                                                'MODERATE': {'description': 'Descriptor '
                                                                                            'is '
                                                                                            'moderately '
                                                                                            'resilient '
                                                                                            'to '
                                                                                            'changes '
                                                                                            '(e.g., '
                                                                                            'CRC '
                                                                                            'sum)',
                                                                             'text': 'MODERATE'},
                                                                'VERY_HIGH': {'description': 'Descriptor '
                                                                                             'is '
                                                                                             'very '
                                                                                             'resilient '
                                                                                             'to '
                                                                                             'changes '
                                                                                             '(e.g., '
                                                                                             'MD5 '
                                                                                             'sum)',
                                                                              'text': 'VERY_HIGH'},
                                                                'VERY_LOW': {'description': 'Descriptor '
                                                                                            'has '
                                                                                            'very '
                                                                                            'low '
                                                                                            'resilience '
                                                                                            'to '
                                                                                            'changes '
                                                                                            '(e.g., '
                                                                                            'length, '
                                                                                            'date '
                                                                                            'or '
                                                                                            'name '
                                                                                            'individually)',
                                                                             'text': 'VERY_LOW'}}}},
     'id': 'https://w3id.org/crystalia',
     'imports': ['linkml:types'],
     'license': 'MIT',
     'metamodel_version': '1.7.0',
     'name': 'crystalia-datamodel',
     'prefixes': {'cryd': {'prefix_prefix': 'cryd',
                           'prefix_reference': 'https://crystalia.link/data/'},
                  'crys': {'prefix_prefix': 'crys',
                           'prefix_reference': 'https://w3id.org/crystalia/'},
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
     'slots': {'comment': {'description': 'A description of the item',
                           'domain_of': ['Method'],
                           'from_schema': 'https://w3id.org/crystalia',
                           'name': 'comment',
                           'range': 'string',
                           'required': False,
                           'slot_uri': 'rdfs:comment'},
               'coverage': {'description': 'The coverage of the descriptor (0.0 to '
                                           '1.0)',
                            'domain_of': ['Descriptor'],
                            'from_schema': 'https://w3id.org/crystalia',
                            'multivalued': False,
                            'name': 'coverage',
                            'range': 'float',
                            'required': True},
               'hasDescriptor': {'description': 'The descriptors associated with '
                                                'an item',
                                 'domain_of': ['DescribableThing'],
                                 'from_schema': 'https://w3id.org/crystalia',
                                 'multivalued': True,
                                 'name': 'hasDescriptor',
                                 'range': 'Descriptor'},
               'hasType': {'description': 'The type of the descriptor',
                           'domain_of': ['Descriptor'],
                           'from_schema': 'https://w3id.org/crystalia',
                           'multivalued': False,
                           'name': 'hasType',
                           'range': 'DescriptorType',
                           'required': True},
               'id': {'description': 'A unique identifier',
                      'domain_of': ['Thing'],
                      'from_schema': 'https://w3id.org/crystalia',
                      'identifier': True,
                      'name': 'id',
                      'range': 'uriorcurie',
                      'required': True},
               'isPartOf': {'description': 'The items in the dataset such as files',
                            'domain_of': ['Item'],
                            'from_schema': 'https://w3id.org/crystalia',
                            'multivalued': False,
                            'name': 'isPartOf',
                            'range': 'uriorcurie',
                            'required': False,
                            'slot_uri': 'dct:isPartOf'},
               'label': {'description': 'A human-readable label for the item, most '
                                        'often the filename',
                         'domain_of': ['Item',
                                       'Descriptor',
                                       'DescriptorType',
                                       'Method'],
                         'from_schema': 'https://w3id.org/crystalia',
                         'name': 'label',
                         'range': 'string',
                         'required': True,
                         'slot_uri': 'rdfs:label'},
               'length': {'description': 'The length of the data described by the '
                                         'descriptor',
                          'domain_of': ['Descriptor'],
                          'from_schema': 'https://w3id.org/crystalia',
                          'multivalued': False,
                          'name': 'length',
                          'range': 'integer',
                          'required': False,
                          'unit': {'ucum_code': 'byte'}},
               'max_block_size': {'description': 'The maximum size of the block of '
                                                 'data described by the descriptor',
                                  'domain_of': ['DescriptorType'],
                                  'from_schema': 'https://w3id.org/crystalia',
                                  'name': 'max_block_size',
                                  'range': 'integer',
                                  'required': False},
               'offset': {'description': 'The starting offset for partial file '
                                         'descriptors',
                          'domain_of': ['Descriptor'],
                          'from_schema': 'https://w3id.org/crystalia',
                          'multivalued': False,
                          'name': 'offset',
                          'range': 'integer',
                          'required': True,
                          'unit': {'ucum_code': 'byte'}},
               'robustness': {'description': 'The robustness category of the '
                                             'descriptor type',
                              'domain_of': ['Method'],
                              'from_schema': 'https://w3id.org/crystalia',
                              'multivalued': False,
                              'name': 'robustness',
                              'range': 'descriptor_robustness',
                              'required': True},
               'usesMethod': {'description': 'The method used to generate the '
                                             'descriptor',
                              'domain_of': ['DescriptorType'],
                              'from_schema': 'https://w3id.org/crystalia',
                              'multivalued': False,
                              'name': 'usesMethod',
                              'range': 'Method',
                              'required': True},
               'value': {'description': 'The value of the descriptor',
                         'domain_of': ['Descriptor'],
                         'from_schema': 'https://w3id.org/crystalia',
                         'multivalued': False,
                         'name': 'value',
                         'range': 'string',
                         'required': True}},
     'source_file': 'src/crystalia_data_model/schema/linkml_crystalia.yaml',
     'title': 'Crystalia Data Model',
     'version': '0.0.1'} )

class DescriptorRobustness(str, Enum):
    """
    Degree of resilience of the descriptor to changes in the item
    """
    EXTREMELY_HIGH = "EXTREMELY_HIGH"
    """
    Descriptor is extremely resilient to changes (e.g., SHA512 sum)
    """
    VERY_HIGH = "VERY_HIGH"
    """
    Descriptor is very resilient to changes (e.g., MD5 sum)
    """
    HIGH = "HIGH"
    """
    Descriptor is highly resilient to changes (e.g., Farmhash, Jenkins hash)
    """
    MODERATE = "MODERATE"
    """
    Descriptor is moderately resilient to changes (e.g., CRC sum)
    """
    LOW = "LOW"
    """
    Descriptor has low resilience to changes (e.g., length + date + name together)
    """
    VERY_LOW = "VERY_LOW"
    """
    Descriptor has very low resilience to changes (e.g., length, date or name individually)
    """



class Thing(ConfiguredBaseModel):
    """
    Anything that has an id
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:Thing',
         'description': 'Anything that has an id',
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'Thing',
         'slots': ['id']})

    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'Thing',
         'range': 'uriorcurie',
         'required': True} })


class DescribableThing(Thing):
    """
    An item that can be described by one or more descriptors. Could be an item(file) or another descriptor
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:DescribableThing',
         'description': 'An item that can be described by one or more descriptors. '
                        'Could be an item(file) or another descriptor',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'Thing',
         'name': 'DescribableThing',
         'slots': ['hasDescriptor']})

    hasDescriptor: Optional[list[str]] = Field(default=None, description="""The descriptors associated with an item""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor',
         'description': 'The descriptors associated with an item',
         'domain_of': ['DescribableThing'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasDescriptor',
         'owner': 'DescribableThing',
         'range': 'Descriptor'} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'DescribableThing',
         'range': 'uriorcurie',
         'required': True} })


class Item(DescribableThing):
    """
    An individual item for example a file
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:Item',
         'description': 'An individual item for example a file',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'DescribableThing',
         'name': 'Item',
         'slots': ['label', 'isPartOf']})

    label: str = Field(default=..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'description': 'A human-readable label for the item, most often the filename',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'label',
         'owner': 'Item',
         'range': 'string',
         'required': True,
         'slot_uri': 'rdfs:label'} })
    isPartOf: Optional[str] = Field(default=None, description="""The items in the dataset such as files""", json_schema_extra = { "linkml_meta": {'alias': 'isPartOf',
         'description': 'The items in the dataset such as files',
         'domain_of': ['Item'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'isPartOf',
         'owner': 'Item',
         'range': 'uriorcurie',
         'required': False,
         'slot_uri': 'dct:isPartOf'} })
    hasDescriptor: Optional[list[str]] = Field(default=None, description="""The descriptors associated with an item""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor',
         'description': 'The descriptors associated with an item',
         'domain_of': ['DescribableThing'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasDescriptor',
         'owner': 'Item',
         'range': 'Descriptor'} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'Item',
         'range': 'uriorcurie',
         'required': True} })


class Descriptor(DescribableThing):
    """
    A descriptor for the whole or part of an item or another descriptor
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'attributes': {'label': {'description': 'A human-readable label',
                                  'domain_of': ['Item',
                                                'Descriptor',
                                                'DescriptorType',
                                                'Method'],
                                  'from_schema': 'https://w3id.org/crystalia',
                                  'name': 'label',
                                  'required': False,
                                  'slot_uri': 'rdfs:label'}},
         'class_uri': 'crys:Descriptor',
         'description': 'A descriptor for the whole or part of an item or another '
                        'descriptor',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'DescribableThing',
         'name': 'Descriptor',
         'slots': ['hasType', 'value', 'offset', 'length', 'coverage']})

    hasType: str = Field(default=..., description="""The type of the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'hasType',
         'description': 'The type of the descriptor',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'hasType',
         'owner': 'Descriptor',
         'range': 'DescriptorType',
         'required': True} })
    value: str = Field(default=..., description="""The value of the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'value',
         'description': 'The value of the descriptor',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'value',
         'owner': 'Descriptor',
         'range': 'string',
         'required': True} })
    offset: int = Field(default=..., description="""The starting offset for partial file descriptors""", json_schema_extra = { "linkml_meta": {'alias': 'offset',
         'description': 'The starting offset for partial file descriptors',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'offset',
         'owner': 'Descriptor',
         'range': 'integer',
         'required': True,
         'unit': {'ucum_code': 'byte'}} })
    length: Optional[int] = Field(default=None, description="""The length of the data described by the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'length',
         'description': 'The length of the data described by the descriptor',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'length',
         'owner': 'Descriptor',
         'range': 'integer',
         'required': False,
         'unit': {'ucum_code': 'byte'}} })
    coverage: float = Field(default=..., description="""The coverage of the descriptor (0.0 to 1.0)""", json_schema_extra = { "linkml_meta": {'alias': 'coverage',
         'description': 'The coverage of the descriptor (0.0 to 1.0)',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'coverage',
         'owner': 'Descriptor',
         'range': 'float',
         'required': True} })
    label: Optional[str] = Field(default=None, description="""A human-readable label""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'description': 'A human-readable label',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'label',
         'owner': 'Descriptor',
         'range': 'string',
         'required': False,
         'slot_uri': 'rdfs:label'} })
    hasDescriptor: Optional[list[str]] = Field(default=None, description="""The descriptors associated with an item""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor',
         'description': 'The descriptors associated with an item',
         'domain_of': ['DescribableThing'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasDescriptor',
         'owner': 'Descriptor',
         'range': 'Descriptor'} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'Descriptor',
         'range': 'uriorcurie',
         'required': True} })


class DescriptorType(Thing):
    """
    Details about a descriptor type
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:DescriptorType',
         'description': 'Details about a descriptor type',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'Thing',
         'name': 'DescriptorType',
         'slots': ['label', 'usesMethod', 'max_block_size']})

    label: str = Field(default=..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'description': 'A human-readable label for the item, most often the filename',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'label',
         'owner': 'DescriptorType',
         'range': 'string',
         'required': True,
         'slot_uri': 'rdfs:label'} })
    usesMethod: str = Field(default=..., description="""The method used to generate the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'usesMethod',
         'description': 'The method used to generate the descriptor',
         'domain_of': ['DescriptorType'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'usesMethod',
         'owner': 'DescriptorType',
         'range': 'Method',
         'required': True} })
    max_block_size: Optional[int] = Field(default=None, description="""The maximum size of the block of data described by the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'max_block_size',
         'description': 'The maximum size of the block of data described by the '
                        'descriptor',
         'domain_of': ['DescriptorType'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'max_block_size',
         'owner': 'DescriptorType',
         'range': 'integer',
         'required': False} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'DescriptorType',
         'range': 'uriorcurie',
         'required': True} })


class Method(Thing):
    """
    A method used to generate a descriptor
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:Method',
         'description': 'A method used to generate a descriptor',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'Thing',
         'name': 'Method',
         'slots': ['label', 'comment', 'robustness']})

    label: str = Field(default=..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'description': 'A human-readable label for the item, most often the filename',
         'domain_of': ['Item', 'Descriptor', 'DescriptorType', 'Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'label',
         'owner': 'Method',
         'range': 'string',
         'required': True,
         'slot_uri': 'rdfs:label'} })
    comment: Optional[str] = Field(default=None, description="""A description of the item""", json_schema_extra = { "linkml_meta": {'alias': 'comment',
         'description': 'A description of the item',
         'domain_of': ['Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'comment',
         'owner': 'Method',
         'range': 'string',
         'required': False,
         'slot_uri': 'rdfs:comment'} })
    robustness: DescriptorRobustness = Field(default=..., description="""The robustness category of the descriptor type""", json_schema_extra = { "linkml_meta": {'alias': 'robustness',
         'description': 'The robustness category of the descriptor type',
         'domain_of': ['Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'robustness',
         'owner': 'Method',
         'range': 'descriptor_robustness',
         'required': True} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'Method',
         'range': 'uriorcurie',
         'required': True} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Thing.model_rebuild()
DescribableThing.model_rebuild()
Item.model_rebuild()
Descriptor.model_rebuild()
DescriptorType.model_rebuild()
Method.model_rebuild()
