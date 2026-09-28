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
version = "2.0.0"


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
                                                                       'Method'],
                                                         'from_schema': 'https://w3id.org/crystalia',
                                                         'name': 'label',
                                                         'required': False,
                                                         'slot_uri': 'rdfs:label'}},
                                'class_uri': 'crys:Descriptor',
                                'description': 'A content-addressed descriptor for '
                                               'the whole or part of an item or '
                                               'another descriptor. Its id is '
                                               'minted by the canonical encoder '
                                               'from its type, its intrinsic '
                                               'fields and its child descriptor '
                                               'ids; coverage is not stored.',
                                'from_schema': 'https://w3id.org/crystalia',
                                'is_a': 'DescribableThing',
                                'name': 'Descriptor',
                                'slots': ['hasType',
                                          'value',
                                          'offset',
                                          'length',
                                          'total',
                                          'assertedCoverage']},
                 'HarvestRecord': {'class_uri': 'crys:HarvestRecord',
                                   'description': 'One record per harvest run: '
                                                  'when it ran, which collector '
                                                  'produced it, where it started, '
                                                  'which methods it used and which '
                                                  'root items it produced.',
                                   'from_schema': 'https://w3id.org/crystalia',
                                   'is_a': 'Thing',
                                   'name': 'HarvestRecord',
                                   'slots': ['startedAt',
                                             'endedAt',
                                             'collectorVersion',
                                             'sourceRoot',
                                             'usesMethod',
                                             'hasRoot']},
                 'Item': {'class_uri': 'crys:Item',
                          'description': 'An individual item for example a file',
                          'from_schema': 'https://w3id.org/crystalia',
                          'is_a': 'DescribableThing',
                          'name': 'Item',
                          'slots': ['label', 'isPartOf']},
                 'Method': {'class_uri': 'crys:Method',
                            'description': 'A method used to generate descriptors. '
                                           'Content-addressed: one node per (name, '
                                           'canonical parameter set), reused '
                                           'across harvests.',
                            'from_schema': 'https://w3id.org/crystalia',
                            'is_a': 'Thing',
                            'name': 'Method',
                            'slots': ['label', 'comment', 'parameters']},
                 'Thing': {'class_uri': 'crys:Thing',
                           'description': 'Anything that has an id',
                           'from_schema': 'https://w3id.org/crystalia',
                           'name': 'Thing',
                           'slots': ['id']}},
     'default_prefix': 'crys',
     'default_range': 'string',
     'description': 'Data model for the Crystalia dataset annotation model.\n'
                    '\n'
                    'v2: descriptors are content-addressed and intrinsic. Coverage '
                    'is never\n'
                    "stored (computed from the descriptor's type by "
                    '`crystalia_data_model.types`);\n'
                    '`offset` is permitted only on positional descriptors; `total` '
                    'only on\n'
                    'region/stream composites; `length` is always the number of '
                    'bytes hashed.\n'
                    'Descriptor type semantics (hierarchy, grade, robustness, '
                    'strength) live in\n'
                    'the Python type registry, not in the schema. Methods are '
                    'content-addressed\n'
                    'and each harvest run is recorded once as a HarvestRecord.',
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
     'slots': {'assertedCoverage': {'description': 'Coverage asserted by an opaque '
                                                   'producer, in [0, 1]. Used only '
                                                   'by the `asserted` descriptor '
                                                   "type; every other type's "
                                                   'coverage is computed.',
                                    'domain_of': ['Descriptor'],
                                    'from_schema': 'https://w3id.org/crystalia',
                                    'maximum_value': 1,
                                    'minimum_value': 0,
                                    'multivalued': False,
                                    'name': 'assertedCoverage',
                                    'range': 'float',
                                    'required': False,
                                    'slot_uri': 'crys:assertedCoverage'},
               'collectorVersion': {'description': 'The version of the collector '
                                                   'that produced the harvest',
                                    'domain_of': ['HarvestRecord'],
                                    'from_schema': 'https://w3id.org/crystalia',
                                    'multivalued': False,
                                    'name': 'collectorVersion',
                                    'range': 'string',
                                    'required': False,
                                    'slot_uri': 'crys:collectorVersion'},
               'comment': {'description': 'A description of the item',
                           'domain_of': ['Method'],
                           'from_schema': 'https://w3id.org/crystalia',
                           'name': 'comment',
                           'range': 'string',
                           'required': False,
                           'slot_uri': 'rdfs:comment'},
               'endedAt': {'description': 'When the harvest ended',
                           'domain_of': ['HarvestRecord'],
                           'from_schema': 'https://w3id.org/crystalia',
                           'multivalued': False,
                           'name': 'endedAt',
                           'range': 'datetime',
                           'required': False,
                           'slot_uri': 'crys:endedAt'},
               'hasDescriptor': {'description': 'The descriptors associated with '
                                                'an item, or the child descriptors '
                                                'of a composite descriptor',
                                 'domain_of': ['DescribableThing'],
                                 'from_schema': 'https://w3id.org/crystalia',
                                 'multivalued': True,
                                 'name': 'hasDescriptor',
                                 'range': 'uriorcurie',
                                 'slot_uri': 'crys:hasDescriptor'},
               'hasRoot': {'description': 'The root items produced by the harvest',
                           'domain_of': ['HarvestRecord'],
                           'from_schema': 'https://w3id.org/crystalia',
                           'multivalued': True,
                           'name': 'hasRoot',
                           'range': 'Item',
                           'required': False,
                           'slot_uri': 'crys:hasRoot'},
               'hasType': {'description': 'The type of the descriptor (a '
                                          '`cryd:desc-type/<name>` IRI resolved by '
                                          'the type registry)',
                           'domain_of': ['Descriptor'],
                           'from_schema': 'https://w3id.org/crystalia',
                           'multivalued': False,
                           'name': 'hasType',
                           'range': 'uriorcurie',
                           'required': True,
                           'slot_uri': 'crys:hasType'},
               'id': {'description': 'A unique identifier',
                      'domain_of': ['Thing'],
                      'from_schema': 'https://w3id.org/crystalia',
                      'identifier': True,
                      'name': 'id',
                      'range': 'uriorcurie',
                      'required': True},
               'isPartOf': {'description': 'The parent item (e.g. the directory '
                                           'containing a file)',
                            'domain_of': ['Item'],
                            'from_schema': 'https://w3id.org/crystalia',
                            'multivalued': False,
                            'name': 'isPartOf',
                            'range': 'Item',
                            'required': False,
                            'slot_uri': 'dct:isPartOf'},
               'label': {'description': 'A human-readable label for the item, most '
                                        'often the filename',
                         'domain_of': ['Item', 'Descriptor', 'Method'],
                         'from_schema': 'https://w3id.org/crystalia',
                         'name': 'label',
                         'range': 'string',
                         'required': True,
                         'slot_uri': 'rdfs:label'},
               'length': {'description': 'The number of bytes hashed. Required on '
                                         'hash descriptors and part of their '
                                         'identity; absent on all other '
                                         'descriptors.',
                          'domain_of': ['Descriptor'],
                          'from_schema': 'https://w3id.org/crystalia',
                          'minimum_value': 0,
                          'multivalued': False,
                          'name': 'length',
                          'range': 'integer',
                          'required': False,
                          'slot_uri': 'crys:length',
                          'unit': {'ucum_code': 'byte'}},
               'offset': {'description': 'The starting byte offset of a positional '
                                         'descriptor. Permitted only on positional '
                                         'descriptors; part of their identity.',
                          'domain_of': ['Descriptor'],
                          'from_schema': 'https://w3id.org/crystalia',
                          'minimum_value': 0,
                          'multivalued': False,
                          'name': 'offset',
                          'range': 'integer',
                          'required': False,
                          'slot_uri': 'crys:offset',
                          'unit': {'ucum_code': 'byte'}},
               'parameters': {'description': 'The canonical parameter string of a '
                                             'method (sorted, length-prefixed '
                                             '`key=len:value` lines). Part of the '
                                             "method's content address.",
                              'domain_of': ['Method'],
                              'from_schema': 'https://w3id.org/crystalia',
                              'multivalued': False,
                              'name': 'parameters',
                              'range': 'string',
                              'required': False,
                              'slot_uri': 'crys:parameters'},
               'sourceRoot': {'description': 'The root the harvest started from '
                                             '(path, URL or bucket prefix)',
                              'domain_of': ['HarvestRecord'],
                              'from_schema': 'https://w3id.org/crystalia',
                              'multivalued': False,
                              'name': 'sourceRoot',
                              'range': 'string',
                              'required': False,
                              'slot_uri': 'crys:sourceRoot'},
               'startedAt': {'description': 'When the harvest started',
                             'domain_of': ['HarvestRecord'],
                             'from_schema': 'https://w3id.org/crystalia',
                             'multivalued': False,
                             'name': 'startedAt',
                             'range': 'datetime',
                             'required': False,
                             'slot_uri': 'crys:startedAt'},
               'total': {'description': 'The number of parts expected by a '
                                        'region/stream composite. Required on '
                                        'region composites, forbidden everywhere '
                                        'else (folder rollups are complete by '
                                        'construction and carry no total).',
                         'domain_of': ['Descriptor'],
                         'from_schema': 'https://w3id.org/crystalia',
                         'minimum_value': 1,
                         'multivalued': False,
                         'name': 'total',
                         'range': 'integer',
                         'required': False,
                         'slot_uri': 'crys:total'},
               'usesMethod': {'description': 'The methods used by the harvest',
                              'domain_of': ['HarvestRecord'],
                              'from_schema': 'https://w3id.org/crystalia',
                              'multivalued': True,
                              'name': 'usesMethod',
                              'range': 'Method',
                              'required': False,
                              'slot_uri': 'crys:usesMethod'},
               'value': {'description': 'The value of the descriptor',
                         'domain_of': ['Descriptor'],
                         'from_schema': 'https://w3id.org/crystalia',
                         'multivalued': False,
                         'name': 'value',
                         'range': 'string',
                         'required': True,
                         'slot_uri': 'crys:value'}},
     'source_file': 'src/crystalia_data_model/schema/linkml_crystalia.yaml',
     'title': 'Crystalia Data Model',
     'version': '2.0.0'} )


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

    hasDescriptor: Optional[list[str]] = Field(default=None, description="""The descriptors associated with an item, or the child descriptors of a composite descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor',
         'description': 'The descriptors associated with an item, or the child '
                        'descriptors of a composite descriptor',
         'domain_of': ['DescribableThing'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasDescriptor',
         'owner': 'DescribableThing',
         'range': 'uriorcurie',
         'slot_uri': 'crys:hasDescriptor'} })
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
         'domain_of': ['Item', 'Descriptor', 'Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'label',
         'owner': 'Item',
         'range': 'string',
         'required': True,
         'slot_uri': 'rdfs:label'} })
    isPartOf: Optional[str] = Field(default=None, description="""The parent item (e.g. the directory containing a file)""", json_schema_extra = { "linkml_meta": {'alias': 'isPartOf',
         'description': 'The parent item (e.g. the directory containing a file)',
         'domain_of': ['Item'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'isPartOf',
         'owner': 'Item',
         'range': 'Item',
         'required': False,
         'slot_uri': 'dct:isPartOf'} })
    hasDescriptor: Optional[list[str]] = Field(default=None, description="""The descriptors associated with an item, or the child descriptors of a composite descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor',
         'description': 'The descriptors associated with an item, or the child '
                        'descriptors of a composite descriptor',
         'domain_of': ['DescribableThing'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasDescriptor',
         'owner': 'Item',
         'range': 'uriorcurie',
         'slot_uri': 'crys:hasDescriptor'} })
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
    A content-addressed descriptor for the whole or part of an item or another descriptor. Its id is minted by the canonical encoder from its type, its intrinsic fields and its child descriptor ids; coverage is not stored.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'attributes': {'label': {'description': 'A human-readable label',
                                  'domain_of': ['Item', 'Descriptor', 'Method'],
                                  'from_schema': 'https://w3id.org/crystalia',
                                  'name': 'label',
                                  'required': False,
                                  'slot_uri': 'rdfs:label'}},
         'class_uri': 'crys:Descriptor',
         'description': 'A content-addressed descriptor for the whole or part of an '
                        'item or another descriptor. Its id is minted by the canonical '
                        'encoder from its type, its intrinsic fields and its child '
                        'descriptor ids; coverage is not stored.',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'DescribableThing',
         'name': 'Descriptor',
         'slots': ['hasType', 'value', 'offset', 'length', 'total', 'assertedCoverage']})

    hasType: str = Field(default=..., description="""The type of the descriptor (a `cryd:desc-type/<name>` IRI resolved by the type registry)""", json_schema_extra = { "linkml_meta": {'alias': 'hasType',
         'description': 'The type of the descriptor (a `cryd:desc-type/<name>` IRI '
                        'resolved by the type registry)',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'hasType',
         'owner': 'Descriptor',
         'range': 'uriorcurie',
         'required': True,
         'slot_uri': 'crys:hasType'} })
    value: str = Field(default=..., description="""The value of the descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'value',
         'description': 'The value of the descriptor',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'value',
         'owner': 'Descriptor',
         'range': 'string',
         'required': True,
         'slot_uri': 'crys:value'} })
    offset: Optional[int] = Field(default=None, description="""The starting byte offset of a positional descriptor. Permitted only on positional descriptors; part of their identity.""", ge=0, json_schema_extra = { "linkml_meta": {'alias': 'offset',
         'description': 'The starting byte offset of a positional descriptor. '
                        'Permitted only on positional descriptors; part of their '
                        'identity.',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'minimum_value': 0,
         'multivalued': False,
         'name': 'offset',
         'owner': 'Descriptor',
         'range': 'integer',
         'required': False,
         'slot_uri': 'crys:offset',
         'unit': {'ucum_code': 'byte'}} })
    length: Optional[int] = Field(default=None, description="""The number of bytes hashed. Required on hash descriptors and part of their identity; absent on all other descriptors.""", ge=0, json_schema_extra = { "linkml_meta": {'alias': 'length',
         'description': 'The number of bytes hashed. Required on hash descriptors and '
                        'part of their identity; absent on all other descriptors.',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'minimum_value': 0,
         'multivalued': False,
         'name': 'length',
         'owner': 'Descriptor',
         'range': 'integer',
         'required': False,
         'slot_uri': 'crys:length',
         'unit': {'ucum_code': 'byte'}} })
    total: Optional[int] = Field(default=None, description="""The number of parts expected by a region/stream composite. Required on region composites, forbidden everywhere else (folder rollups are complete by construction and carry no total).""", ge=1, json_schema_extra = { "linkml_meta": {'alias': 'total',
         'description': 'The number of parts expected by a region/stream composite. '
                        'Required on region composites, forbidden everywhere else '
                        '(folder rollups are complete by construction and carry no '
                        'total).',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'minimum_value': 1,
         'multivalued': False,
         'name': 'total',
         'owner': 'Descriptor',
         'range': 'integer',
         'required': False,
         'slot_uri': 'crys:total'} })
    assertedCoverage: Optional[float] = Field(default=None, description="""Coverage asserted by an opaque producer, in [0, 1]. Used only by the `asserted` descriptor type; every other type's coverage is computed.""", ge=0, le=1, json_schema_extra = { "linkml_meta": {'alias': 'assertedCoverage',
         'description': 'Coverage asserted by an opaque producer, in [0, 1]. Used only '
                        "by the `asserted` descriptor type; every other type's "
                        'coverage is computed.',
         'domain_of': ['Descriptor'],
         'from_schema': 'https://w3id.org/crystalia',
         'maximum_value': 1,
         'minimum_value': 0,
         'multivalued': False,
         'name': 'assertedCoverage',
         'owner': 'Descriptor',
         'range': 'float',
         'required': False,
         'slot_uri': 'crys:assertedCoverage'} })
    label: Optional[str] = Field(default=None, description="""A human-readable label""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'description': 'A human-readable label',
         'domain_of': ['Item', 'Descriptor', 'Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'name': 'label',
         'owner': 'Descriptor',
         'range': 'string',
         'required': False,
         'slot_uri': 'rdfs:label'} })
    hasDescriptor: Optional[list[str]] = Field(default=None, description="""The descriptors associated with an item, or the child descriptors of a composite descriptor""", json_schema_extra = { "linkml_meta": {'alias': 'hasDescriptor',
         'description': 'The descriptors associated with an item, or the child '
                        'descriptors of a composite descriptor',
         'domain_of': ['DescribableThing'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasDescriptor',
         'owner': 'Descriptor',
         'range': 'uriorcurie',
         'slot_uri': 'crys:hasDescriptor'} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'Descriptor',
         'range': 'uriorcurie',
         'required': True} })


class Method(Thing):
    """
    A method used to generate descriptors. Content-addressed: one node per (name, canonical parameter set), reused across harvests.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:Method',
         'description': 'A method used to generate descriptors. Content-addressed: one '
                        'node per (name, canonical parameter set), reused across '
                        'harvests.',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'Thing',
         'name': 'Method',
         'slots': ['label', 'comment', 'parameters']})

    label: str = Field(default=..., description="""A human-readable label for the item, most often the filename""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'description': 'A human-readable label for the item, most often the filename',
         'domain_of': ['Item', 'Descriptor', 'Method'],
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
    parameters: Optional[str] = Field(default=None, description="""The canonical parameter string of a method (sorted, length-prefixed `key=len:value` lines). Part of the method's content address.""", json_schema_extra = { "linkml_meta": {'alias': 'parameters',
         'description': 'The canonical parameter string of a method (sorted, '
                        "length-prefixed `key=len:value` lines). Part of the method's "
                        'content address.',
         'domain_of': ['Method'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'parameters',
         'owner': 'Method',
         'range': 'string',
         'required': False,
         'slot_uri': 'crys:parameters'} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'Method',
         'range': 'uriorcurie',
         'required': True} })


class HarvestRecord(Thing):
    """
    One record per harvest run: when it ran, which collector produced it, where it started, which methods it used and which root items it produced.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'crys:HarvestRecord',
         'description': 'One record per harvest run: when it ran, which collector '
                        'produced it, where it started, which methods it used and '
                        'which root items it produced.',
         'from_schema': 'https://w3id.org/crystalia',
         'is_a': 'Thing',
         'name': 'HarvestRecord',
         'slots': ['startedAt',
                   'endedAt',
                   'collectorVersion',
                   'sourceRoot',
                   'usesMethod',
                   'hasRoot']})

    startedAt: Optional[datetime ] = Field(default=None, description="""When the harvest started""", json_schema_extra = { "linkml_meta": {'alias': 'startedAt',
         'description': 'When the harvest started',
         'domain_of': ['HarvestRecord'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'startedAt',
         'owner': 'HarvestRecord',
         'range': 'datetime',
         'required': False,
         'slot_uri': 'crys:startedAt'} })
    endedAt: Optional[datetime ] = Field(default=None, description="""When the harvest ended""", json_schema_extra = { "linkml_meta": {'alias': 'endedAt',
         'description': 'When the harvest ended',
         'domain_of': ['HarvestRecord'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'endedAt',
         'owner': 'HarvestRecord',
         'range': 'datetime',
         'required': False,
         'slot_uri': 'crys:endedAt'} })
    collectorVersion: Optional[str] = Field(default=None, description="""The version of the collector that produced the harvest""", json_schema_extra = { "linkml_meta": {'alias': 'collectorVersion',
         'description': 'The version of the collector that produced the harvest',
         'domain_of': ['HarvestRecord'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'collectorVersion',
         'owner': 'HarvestRecord',
         'range': 'string',
         'required': False,
         'slot_uri': 'crys:collectorVersion'} })
    sourceRoot: Optional[str] = Field(default=None, description="""The root the harvest started from (path, URL or bucket prefix)""", json_schema_extra = { "linkml_meta": {'alias': 'sourceRoot',
         'description': 'The root the harvest started from (path, URL or bucket '
                        'prefix)',
         'domain_of': ['HarvestRecord'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': False,
         'name': 'sourceRoot',
         'owner': 'HarvestRecord',
         'range': 'string',
         'required': False,
         'slot_uri': 'crys:sourceRoot'} })
    usesMethod: Optional[list[str]] = Field(default=None, description="""The methods used by the harvest""", json_schema_extra = { "linkml_meta": {'alias': 'usesMethod',
         'description': 'The methods used by the harvest',
         'domain_of': ['HarvestRecord'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'usesMethod',
         'owner': 'HarvestRecord',
         'range': 'Method',
         'required': False,
         'slot_uri': 'crys:usesMethod'} })
    hasRoot: Optional[list[str]] = Field(default=None, description="""The root items produced by the harvest""", json_schema_extra = { "linkml_meta": {'alias': 'hasRoot',
         'description': 'The root items produced by the harvest',
         'domain_of': ['HarvestRecord'],
         'from_schema': 'https://w3id.org/crystalia',
         'multivalued': True,
         'name': 'hasRoot',
         'owner': 'HarvestRecord',
         'range': 'Item',
         'required': False,
         'slot_uri': 'crys:hasRoot'} })
    id: str = Field(default=..., description="""A unique identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'description': 'A unique identifier',
         'domain_of': ['Thing'],
         'from_schema': 'https://w3id.org/crystalia',
         'identifier': True,
         'name': 'id',
         'owner': 'HarvestRecord',
         'range': 'uriorcurie',
         'required': True} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Thing.model_rebuild()
DescribableThing.model_rebuild()
Item.model_rebuild()
Descriptor.model_rebuild()
Method.model_rebuild()
HarvestRecord.model_rebuild()
