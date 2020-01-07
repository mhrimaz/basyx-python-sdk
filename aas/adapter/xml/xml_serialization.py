# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
Module for serializing Asset Administration Shell data to the official XML format

Note for devs [29.12.2019]: This is currently very badly under construction and will probably be subject to a lot of
                            change. Please overlook everything that doesn't work and is wrong for the moment
"""

import xml.etree.ElementTree as ElTree
from typing import List, Dict, Iterator
import inspect
import base64

from aas import model


# ##############################################################
# functions and classes to manipulate ElTree.Elements more effectively
# ##############################################################


class PyAASXMLSerializationError(Exception):
    """
    Raised when something went wrong during serialization
    """
    pass


def find_rec(parent: ElTree.Element, tag: str) -> Iterator[ElTree.Element]:
    """
    Finds all elements recursively that have the given tag

    todo: Check if this really works as intended

    :param parent: ElTree.Element object to search through
    :param tag: tag of the ElTree.Element to find
    :return: List of ElTree.Elements that have the tag
    """
    for item in parent.findall(tag):
        yield item
    for item in parent:
        find_rec(item, tag)


def update_element(old_element: ElTree.Element,
                   new_element: ElTree.Element) -> ElTree.Element:
    """
    update an existing ElTree.Element with a new ElTree.Elements

    The new_element can be a child, or sub..-child of the old_element.
    ToDo: Check if this works as expected

    :param old_element: Element to update
    :param new_element: ElTree.Element with the data for update
    :return: ElTree.Element with the updated information
    """
    elements_to_update = list(find_rec(old_element, new_element.tag))  # search for elements that match new_element
    if len(elements_to_update) > 1:  # more than one element found that matches with new_element, sth went wrong.
        raise PyAASXMLSerializationError("Found " + str(len(elements_to_update)) + " elements [" + new_element.tag +
                                         "] in " + old_element.tag + ". Expected 1")
    if elements_to_update is not []:  # if the element already exists, remove the outdated element
        old_element.remove(elements_to_update[0])
    old_element.insert(0, new_element)  # insert the new_element
    return old_element


# ##############################################################
# dicts to serialize enum classes to xml
# ##############################################################


MODELING_KIND: Dict[model.ModelingKind, str] = {
    model.ModelingKind.TEMPLATE: 'Template',
    model.ModelingKind.INSTANCE: 'Instance'}

ASSET_KIND: Dict[model.AssetKind, str] = {
    model.AssetKind.TYPE: 'Type',
    model.AssetKind.INSTANCE: 'Instance'}

KEY_ELEMENTS: Dict[model.KeyElements, str] = {
    model.KeyElements.ASSET: 'Asset',
    model.KeyElements.ASSET_ADMINISTRATION_SHELL: 'AssetAdministrationShell',
    model.KeyElements.CONCEPT_DESCRIPTION: 'ConceptDescription',
    model.KeyElements.SUBMODEL: 'Submodel',
    model.KeyElements.ANNOTATED_RELATIONSHIP_ELEMENT: 'AnnotatedRelationshipElement',
    model.KeyElements.BASIC_EVENT: 'BasicEvent',
    model.KeyElements.BLOB: 'Blob',
    model.KeyElements.CAPABILITY: 'Capability',
    model.KeyElements.CONCEPT_DICTIONARY: 'ConceptDictionary',
    model.KeyElements.DATA_ELEMENT: 'DataElement',
    model.KeyElements.ENTITY: 'Entity',
    model.KeyElements.EVENT: 'Event',
    model.KeyElements.FILE: 'File',
    model.KeyElements.MULTI_LANGUAGE_PROPERTY: 'MultiLanguageProperty',
    model.KeyElements.OPERATION: 'Operation',
    model.KeyElements.PROPERTY: 'Property',
    model.KeyElements.RANGE: 'Range',
    model.KeyElements.REFERENCE_ELEMENT: 'ReferenceElement',
    model.KeyElements.RELATIONSHIP_ELEMENT: 'RelationshipElement',
    model.KeyElements.SUBMODEL_ELEMENT: 'SubmodelElement',
    model.KeyElements.SUBMODEL_ELEMENT_COLLECTION: 'SubmodelElementCollection',
    model.KeyElements.VIEW: 'View',
    model.KeyElements.GLOBAL_REFERENCE: 'GlobalReference',
    model.KeyElements.FRAGMENT_REFERENCE: 'FragmentReference'}

KEY_TYPES: Dict[model.KeyType, str] = {
    model.KeyType.CUSTOM: 'Custom',
    model.KeyType.IRDI: 'IRDI',
    model.KeyType.IRI: 'IRI',
    model.KeyType.IDSHORT: 'IdShort',
    model.KeyType.FRAGMENT_ID: 'FragmentId'}

IDENTIFIER_TYPES: Dict[model.IdentifierType, str] = {
    model.IdentifierType.CUSTOM: 'Custom',
    model.IdentifierType.IRDI: 'IRDI',
    model.IdentifierType.IRI: 'IRI'}

ENTITY_TYPES: Dict[model.EntityType, str] = {
    model.EntityType.CO_MANAGED_ENTITY: 'CoManagedEntity',
    model.EntityType.SELF_MANAGED_ENTITY: 'SelfManagedEntity'}


# ##############################################################
# transformation functions to serialize abstract classes from model.base
# ##############################################################
# todo: This doesn't work as intended yet.


def abstract_classes_to_xml(obj: object) -> List[ElTree.Element]:
    """
    transformation function to serialize abstract classes from model.base which are inherited by many classes.

    If the object obj is inheriting from an abstract class, this function returns the serialized information from that
    abstract class in form of ElementTree objects in a list.

    todo: Does order matter? if not, then maybe use a set instead.s

    :param obj: an object of the AAS
    :return: a list of ElementTree.Elements to be inserted into the parent Element of the object
    """
    elements: List[ElTree.Element] = []
    if isinstance(obj, model.Referable):
        et_id_short = ElTree.Element("idShort")
        et_id_short.text = obj.id_short
        elements += [et_id_short]
        if obj.category:
            et_category = ElTree.Element("category")
            et_category.text = obj.category
            elements += [et_category]
        if obj.description:
            et_description = ElTree.Element("description")
            et_description.insert(0, lang_string_set_to_xml(obj.description))
            elements += [et_description]
        if obj.parent:  # todo: Why was this missing in the json implementation?
            et_parent = ElTree.Element("parent")
            # et_reference = reference_to_xml(obj.parent)  # todo: obj.parent is of type Namespace and not Reference
            # et_parent.insert(0, et_reference)
            elements += [et_parent]
        try:  # todo: What does this do? What do we need it for?
            ref_type = next(iter(t for t in inspect.getmro(type(obj)) if t in model.KEY_ELEMENTS_CLASSES))
        except StopIteration as e:
            raise TypeError("Object of type {} is Referable but does not inherit from a known AAS type"
                            .format(obj.__class__.__name__)) from e
        et_model_type = ElTree.Element("modelType")
        et_model_type.text = ref_type.__name__
        elements += [et_model_type]

    if isinstance(obj, model.Identifiable):
        et_identifiable = ElTree.Element("identification")
        et_identifiable.set("idType", IDENTIFIER_TYPES[obj.identification.id_type])
        et_identifiable.text = obj.identification.id
        elements += [et_identifiable]
        if obj.administration:
            et_administration = ElTree.Element("administration")
            et_administration_version = ElTree.Element("version")
            et_administration_version.text = obj.administration.version
            et_administration_revision = ElTree.Element("revision")
            et_administration_revision.text = obj.administration.revision
            et_administration.insert(0, et_administration_version)
            et_administration.insert(1, et_administration_revision)
            elements += [et_administration]

    if isinstance(obj, model.HasDataSpecification):
        if obj.data_specification:
            et_has_data_specification = ElTree.Element("embeddedDataSpecification")
            et_data_specification_content = ElTree.Element("dataSpecificationContent")
            # todo: implement dataSpecificationContent
            et_has_data_specification.insert(0, et_data_specification_content)
            # et_ds_reference = reference_to_xml(obj.data_specification)
            # et_has_data_specification.insert(1, et_ds_reference)
            # todo: data_specification is Set[Reference]. Schema expects optional Reference
            elements += [et_has_data_specification]

    if isinstance(obj, model.HasSemantics):
        if obj.semantic_id:
            et_semantics = ElTree.Element("semanticId")
            et_semantics.insert(0, reference_to_xml(obj.semantic_id))
            elements += [et_semantics]

    if isinstance(obj, model.HasKind):
        if obj.kind is model.ModelingKind.TEMPLATE:
            et_modeling_kind = ElTree.Element("modelingKind")
            et_modeling_kind.text = MODELING_KIND[obj.kind]
            elements += [et_modeling_kind]

    if isinstance(obj, model.Qualifiable):
        if obj.qualifier:
            et_qualifiers = ElTree.Element("qualifier")
            # et_qualifiers.text = obj.qualifier  # todo: find out about constraints, this seems not yet implemented
            elements += [et_qualifiers]

    return elements


# ##############################################################
# transformation functions to serialize classes from model.base
# ##############################################################


def lang_string_set_to_xml(obj: model.LangStringSet) -> ElTree.Element:
    """
    serialization of objects of class LangStringSet to XML

    :param obj: object of class LangStringSet
    :return: serialized ElementTree object
    """
    et_lss = ElTree.Element("langStringSet")
    for language in obj:
        et_lang_string = ElTree.Element("langString")
        et_lang_string.set("lang", language)
        et_lang_string.text = obj[language]
        et_lss.insert(0, et_lang_string)
    return et_lss


def key_to_xml(obj: model.Key) -> ElTree.Element:
    """
    serialization of objects of class Key to XML

    :param obj: object of class Key
    :return: serialized ElementTree object
    """
    et_key = ElTree.Element("key")
    for i in abstract_classes_to_xml(obj):
        et_key.insert(0, i)
    et_key.set("type", KEY_ELEMENTS[obj.type_])
    et_key.set("local", str(obj.local))

    et_id_type = ElTree.Element("idType")
    et_id_type.text = KEY_TYPES[obj.id_type]
    et_key = update_element(et_key, et_id_type)

    et_value = ElTree.Element("keyValue")  # todo: is this correct? couldn't find it in the schema
    et_value.text = obj.value
    et_key = update_element(et_key, et_value)
    return et_key


def administrative_information_to_xml(obj: model.AdministrativeInformation) -> ElTree.Element:
    """
    serialization of objects of class AdministrativeInformation to XML

    :param obj: object of class AdministrativeInformation
    :return: serialized ElementTree object
    """
    et_administration = ElTree.Element("administration")
    for i in abstract_classes_to_xml(obj):
        et_administration.insert(0, i)
    if obj.version:
        et_administration_version = ElTree.Element("version")
        et_administration_version.text = obj.version
        et_administration = update_element(et_administration, et_administration_version)
        if obj.revision:
            et_administration_revision = ElTree.Element("revision")
            et_administration_revision.text = obj.revision
            et_administration = update_element(et_administration, et_administration_revision)
    return et_administration


def identifier_to_xml(obj: model.Identifier) -> ElTree.Element:
    """
    serialization of objects of class Identifier to XML

    :param obj: object of class Identifier
    :return: serialized ElementTree object
    """
    et_identifier = ElTree.Element("identification")
    for i in abstract_classes_to_xml(obj):
        et_identifier.insert(0, i)
    et_id = ElTree.Element("id")
    et_id.text = obj.id
    et_id_type = ElTree.Element("idType")
    et_id_type.text = IDENTIFIER_TYPES[obj.id_type]
    et_identifier.insert(0, et_id_type)
    et_identifier.insert(0, et_id)
    return et_identifier


def reference_to_xml(obj: model.Reference) -> ElTree.Element:
    """
    serialization of objects of class Reference to XML

    :param obj: object of class Reference
    :return: serialized ElementTree object
    """
    et_keys = ElTree.Element("keys")
    for aas_key in obj.key:
        et_key = key_to_xml(aas_key)
        et_keys.insert(0, et_key)
    return et_keys


def constraint_to_xml(obj: model.Constraint) -> ElTree.Element:
    """
    serialization of objects of class Constraint to XML

    TODO: This isn't implemented according to the schema yet

    :param obj: object of class Constraint
    :return: serialized ElementTree object
    """
    constraint_classes = [model.Qualifier, model.Formula]
    et_constraint = ElTree.Element("constraint")
    try:
        const_type = next(iter(t for t in inspect.getmro(type(obj)) if t in constraint_classes))
    except StopIteration as e:
        raise TypeError("Object of type {} is a Constraint but does not inherit from a known AAS Constraint type"
                        .format(obj.__class__.__name__)) from e
    et_constraint.set("modelType", const_type.__name__)
    return et_constraint


def namespace_to_xml(obj: model.Namespace) -> ElTree.Element:
    """
    serialization of objects of class Namespace to XML

    todo: Since this is not yet part of the Details of the AAS model, it's not entirely clear how to serialize this

    :param obj: object of class Namespace
    :return: serialized ElementTree Object
    """
    et_namespace = ElTree.Element("namespace")
    for i in abstract_classes_to_xml(obj):
        et_namespace.insert(0, i)
    return et_namespace


def formula_to_xml(obj: model.Formula) -> ElTree.Element:
    """
    serialization of objects of class Formula to XML

    :param obj: object of class Formula
    :return: serialized ElementTree object
    """
    et_formula = ElTree.Element("formula")
    for i in abstract_classes_to_xml(obj):
        et_formula.insert(0, i)
    et_constraint = constraint_to_xml(obj)
    et_formula = update_element(et_formula, et_constraint)
    if obj.depends_on:
        et_depends_on = ElTree.Element("dependsOnRefs")
        for aas_reference in obj.depends_on:
            et_ref = reference_to_xml(aas_reference)
            et_depends_on.insert(0, et_ref)
        et_formula.insert(0, et_depends_on)
    return et_formula


def qualifier_to_xml(obj: model.Qualifier) -> ElTree.Element:
    """
    serialization of objects of class Qualifier to XML

    :param obj: object of class Qualifier
    :return: serialized ElementTreeObject
    """
    et_qualifier = ElTree.Element("qualifier")
    for i in abstract_classes_to_xml(obj):
        et_qualifier.insert(0, i)
    et_constraint = constraint_to_xml(obj)
    et_qualifier = update_element(et_qualifier, et_constraint)
    if obj.value:
        et_value = ElTree.Element("value")
        et_value.text = obj.value  # should be a string, since ValueDataType is a string
        et_qualifier.insert(0, et_value)
    if obj.value_id:
        et_value_id = ElTree.Element("valueId")
        et_value_id.insert(0, reference_to_xml(obj.value_id))
        et_qualifier.insert(0, et_value_id)
    et_value_type = ElTree.Element("valueType")
    et_value_type.text = obj.value_type  # should be a string, so no problems
    et_qualifier.insert(0, et_value_type)

    et_type = ElTree.Element("type")
    et_type.text = obj.type_  # should be a string as well
    et_qualifier.insert(0, et_type)

    return et_qualifier


def value_reference_pair_to_xml(obj: model.ValueReferencePair) -> ElTree.Element:
    """
    serialization of objects of class ValueReferencePair to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: object of class ValueReferencePair
    :return: serialized ElementTree object
    """
    et_vrp = ElTree.Element("valueReferencePair")
    for i in abstract_classes_to_xml(obj):
        et_vrp.insert(0, i)
    et_value = ElTree.Element("value")
    et_value.text = obj.value  # since obj.value is of type ValueDataType, which is a string, it should be fine
    et_vrp.insert(0, et_value)
    et_value_id = ElTree.Element("valueId")
    et_value_id.insert(0, reference_to_xml(obj.value_id))  # obj.value_id is a Reference
    et_vrp.insert(0, et_value_id)
    return et_vrp


def value_list_to_xml(obj: model.ValueList) -> ElTree.Element:
    """
    serialization of objects of class ValueList to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: object of class ValueList
    :return: serialized ElementTree object
    """
    et_vl = ElTree.Element("valueList")
    for i in abstract_classes_to_xml(obj):
        et_vl.insert(0, i)
    for aas_reference_pair in obj.value_reference_pair_type:
        et_value_reference_pair = value_reference_pair_to_xml(aas_reference_pair)
        et_vl.insert(0, et_value_reference_pair)
    return et_vl


# ##############################################################
# transformation functions to serialize classes from model.aas
# ##############################################################


def view_to_xml(obj: model.View) -> ElTree.Element:
    """
    serialization of objects of class View to XML

    :param obj: object of class View
    :return: serialized ElementTree object
    """
    et_view = ElTree.Element("View")
    for i in abstract_classes_to_xml(obj):
        et_view.insert(0, i)
    if obj.contained_element:
        et_contained_elements = ElTree.Element("containedElements")
        for contained_element in obj.contained_element:
            et_reference = reference_to_xml(contained_element)
            et_contained_elements.insert(0, et_reference)
    return et_view


def asset_to_xml(obj: model.Asset) -> ElTree.Element:
    """
    serialization of objects of class Asset to XML

    :param obj: object of class Asset
    :return: serialized ElementTree object
    """
    et_asset = ElTree.Element("asset")
    for i in abstract_classes_to_xml(obj):
        et_asset.insert(0, i)
    et_kind = ElTree.Element("kind")
    et_kind.text = ASSET_KIND[obj.kind]
    et_asset.insert(0, et_kind)
    if obj.asset_identification_model:
        et_asset_identification_model = ElTree.Element("assetIdentificationModelRef")
        et_reference = reference_to_xml(obj.asset_identification_model)
        et_asset_identification_model.insert(0, et_reference)
        et_asset.insert(0, et_asset_identification_model)
    if obj.bill_of_material:
        et_bill_of_material = ElTree.Element("billOfMaterialRef")
        et_reference_bom = reference_to_xml(obj.bill_of_material)
        et_bill_of_material.insert(0, et_reference_bom)
        et_asset.insert(0, et_bill_of_material)
    return et_asset


def concept_description_to_xml(obj: model.ConceptDescription) -> ElTree.Element:
    """
    serialization of objects of class ConceptDescription to XML

    :param obj: object of class ConceptDescription
    :return: serialized ElementTree object
    """
    et_concept_description = ElTree.Element("ConceptDescription")
    for i in abstract_classes_to_xml(obj):
        et_concept_description.insert(0, i)
    if obj.is_case_of:
        et_is_case_of = ElTree.Element("isCaseOf")
        for reference in obj.is_case_of:
            et_reference = reference_to_xml(reference)
            et_is_case_of.insert(0, et_reference)
        et_concept_description.insert(0, et_is_case_of)
    return et_concept_description


def concept_dictionary_to_xml(obj: model.ConceptDictionary) -> ElTree.Element:
    """
    serialization of objects of class ConceptDictionary to XML

    :param obj: object of class ConceptDictionary
    :return: serialized ElementTree object
    """
    et_concept_dictionary = ElTree.Element("conceptDictionary")
    for i in abstract_classes_to_xml(obj):
        et_concept_dictionary.insert(0, i)
    if obj.concept_description:
        et_concept_descriptions = ElTree.Element("conceptDescriptionRefs")
        for reference in obj.concept_description:
            et_concept_description_ref = ElTree.Element("conceptDescriptionRef")
            et_reference = reference_to_xml(reference)
            et_concept_description_ref.insert(0, et_reference)
            et_concept_descriptions.insert(0, et_concept_description_ref)
        et_concept_dictionary.insert(0, et_concept_descriptions)
    return et_concept_dictionary


def asset_administration_shell_to_xml(obj: model.AssetAdministrationShell) -> ElTree.Element:
    """
    serialization of objects of class AssetAdministrationShell to XML

    :param obj: object of class AssetAdministrationShell
    :return: serialized ElementTree object
    """
    et_aas = ElTree.Element("assetAdministrationShell")
    for i in abstract_classes_to_xml(obj):
        et_aas.insert(0, i)
    et_namespace = namespace_to_xml(obj)
    et_aas = update_element(et_aas, et_namespace)
    if obj.derived_from:
        et_derived_from = ElTree.Element("derivedFrom")
        et_reference = reference_to_xml(obj.derived_from)
        et_derived_from.insert(0, et_reference)
        et_aas.insert(0, et_derived_from)
    et_asset = ElTree.Element("assetRef")
    et_ref_asset = reference_to_xml(obj.asset)
    et_asset.insert(0, et_ref_asset)
    et_aas.insert(0, et_asset)
    if obj.submodel_:
        et_submodels = ElTree.Element("submodelRefs")
        for reference in obj.submodel_:
            et_ref_sub = reference_to_xml(reference)
            et_submodels.insert(0, et_ref_sub)
        et_aas.insert(0, et_submodels)
    if obj.view:
        et_views = ElTree.Element("views")
        for view in obj.view:
            et_view = view_to_xml(view)
            et_views.insert(0, et_view)
        et_aas.insert(0, et_views)
    if obj.concept_dictionary:
        et_concept_dictionaries = ElTree.Element("conceptDictionaries")
        for concept_dictionary in obj.concept_dictionary:
            et_concept_dictionary = concept_dictionary_to_xml(concept_dictionary)
            et_concept_dictionaries.insert(0, et_concept_dictionary)
        et_aas.insert(0, et_concept_dictionaries)
    if obj.security_:
        et_security = ElTree.Element("security")
        # todo: Since Security is not implemented, add serialization here
        et_aas.insert(0, et_security)
    return et_aas


# ##############################################################
# transformation functions to serialize classes from model.security
# ##############################################################


def security_to_xml(obj: model.Security) -> ElTree.Element:
    """
    serialization of objects of class Security to XML

    :param obj: object of class Security
    :return: serialized ElementTree object
    """
    et_security = ElTree.Element("security")
    for i in abstract_classes_to_xml(obj):
        et_security.insert(0, i)
    return et_security


# ##############################################################
# transformation functions to serialize classes from model.submodel
# ##############################################################


def submodel_element_to_xml(obj: model.SubmodelElement) -> ElTree.Element:
    """
    serialization of objects of class SubmodelElement to XML

    todo: this seems to miss in the json implementation? Because it consists only of inherited parameters?

    :param obj: object of class SubmodelElement
    :return: serialized ElementTree object
    """
    et_submodel_element = ElTree.Element("submodelElement")
    for i in abstract_classes_to_xml(obj):
        et_submodel_element.insert(0, i)
    return et_submodel_element


def submodel_to_xml(obj: model.Submodel) -> ElTree.Element:
    """
    serialization of objects of class Submodel to XML

    :param obj: object of class Submodel
    :return: serialized ElementTree object
    """
    et_submodel = ElTree.Element("submodel")
    for i in abstract_classes_to_xml(obj):
        et_submodel.insert(0, i)
    if obj.submodel_element:
        et_submodel_elements = ElTree.Element("submodelElements")
        for submodel_element in obj.submodel_element:
            et_submodel_element = submodel_element_to_xml(submodel_element)
            et_submodel_elements.insert(0, et_submodel_element)
        et_submodel.insert(0, et_submodel_elements)
    return et_submodel


def data_element_to_xml(obj: model.DataElement) -> ElTree.Element:
    """
    serialization of objects of class DataElement to XML

    :param obj: object of class DataElement
    :return: serialized ElementTree object
    """
    et_data_element = ElTree.Element("dataElement")
    for i in abstract_classes_to_xml(obj):
        et_data_element.insert(0, i)
    return et_data_element


def property_to_xml(obj: model.Property) -> ElTree.Element:
    """
    serialization of objects of class Property to XML

    :param obj: object of class Property
    :return: serialized ElementTree object
    """
    et_property = ElTree.Element("property")
    for i in abstract_classes_to_xml(obj):
        et_property.insert(0, i)
    et_value = ElTree.Element("value")
    et_value.text = obj.value
    et_property.insert(0, et_value)
    if obj.value_id:
        et_value_id = ElTree.Element("valueId")
        et_reference = reference_to_xml(obj.value_id)
        et_value_id.insert(0, et_reference)
        et_value.insert(0, et_value_id)
    et_value_type = ElTree.Element("valueType")
    et_value_type.text = obj.value_type
    et_value.insert(0, et_value_type)
    return et_value


def multi_language_property_to_xml(obj: model.MultiLanguageProperty) -> ElTree.Element:
    """
    serialization of objects of class MultiLanguageProperty to XML

    :param obj: object of class MultiLanguageProperty
    :return: serialized ElementTree object
    """
    et_multi_language_property = ElTree.Element("multiLanguageProperty")
    for i in abstract_classes_to_xml(obj):
        et_multi_language_property.insert(0, i)
    if obj.value:
        et_value = ElTree.Element("value")
        et_lang_string_set = lang_string_set_to_xml(obj.value)
        et_value.insert(0, et_lang_string_set)
        et_multi_language_property.insert(0, et_value)
    if obj.value_id:
        et_value_id = ElTree.Element("valueId")
        et_reference = reference_to_xml(obj.value_id)
        et_value_id.insert(0, et_reference)
        et_multi_language_property.insert(0, et_value_id)
    return et_multi_language_property


def range_to_xml(obj: model.Range) -> ElTree.Element:
    """
    serialization of objects of class Range to XML

    :param obj: object of class Range
    :return: serialized ElementTree object
    """
    et_range = ElTree.Element("range")
    for i in abstract_classes_to_xml(obj):
        et_range.insert(0, i)
    et_value_type = ElTree.Element("valueType")
    et_value_type.text = obj.value_type
    et_range = update_element(et_range, et_value_type)

    et_min = ElTree.Element("min")
    et_min.text = obj.min_
    et_range = update_element(et_range, et_min)

    et_max = ElTree.Element("max")
    et_max.text = obj.max_
    et_range = update_element(et_range, et_max)

    return et_range


def blob_to_xml(obj: model.Blob) -> ElTree.Element:
    """
    serialization of objects of class Blob to XML

    :param obj: object of class Blob
    :return: serialized ElementTree object
    """
    et_blob = ElTree.Element("blob")
    for i in abstract_classes_to_xml(obj):
        et_blob.insert(0, i)
    et_mime_type = ElTree.Element("mimeType")
    et_mime_type.text = obj.mime_type  # base.MimeType = str
    et_blob.insert(0, et_mime_type)

    et_value = ElTree.Element("value")
    if obj.value is not None:
        et_value.text = base64.b64encode(obj.value).decode()
    et_blob.insert(0, et_value)

    return et_blob


def file_to_xml(obj: model.File) -> ElTree.Element:
    """
    serialization of objects of class File to XML

    :param obj: object of class File
    :return: serialized ElementTree object
    """
    et_file = ElTree.Element("file")
    for i in abstract_classes_to_xml(obj):
        et_file.insert(0, i)
    et_value = ElTree.Element("value")
    et_value.text = obj.value  # base.PathType = str
    et_file = update_element(et_file, et_value)

    et_mime_type = ElTree.Element("mimeType")
    et_mime_type.text = obj.mime_type
    et_file = update_element(et_file, et_mime_type)

    return et_file


def reference_element_to_xml(obj: model.ReferenceElement) -> ElTree.Element:
    """
    serialization of objects of class ReferenceElement to XMl

    :param obj: object of class ReferenceElement
    :return: serialized ElementTree object
    """
    et_reference_element = ElTree.Element("referenceElement")
    for i in abstract_classes_to_xml(obj):
        et_reference_element.insert(0, i)
    if obj.value:
        et_value = ElTree.Element("value")
        et_ref = reference_to_xml(obj.value)
        et_value.insert(0, et_ref)
        et_reference_element.insert(0, et_value)
    return et_reference_element


def submodel_element_collection_to_xml(obj: model.SubmodelElementCollection) -> ElTree.Element:
    """
    serialization of objects of class SubmodelElementCollection to XML

    Note that we do not have parameter "allowDuplicates" in out implementation

    :param obj: object of class SubmodelElementCollection
    :return: serialized ElementTree object
    """
    et_submodel_element_collection = ElTree.Element("submodelElementCollection")
    for i in abstract_classes_to_xml(obj):
        et_submodel_element_collection.insert(0, i)
    if obj.value:
        et_value = ElTree.Element("value")
        for submodel_element in obj.value:
            et_submodel_element = submodel_element_to_xml(submodel_element)
            et_value.insert(0, et_submodel_element)
        et_submodel_element_collection.insert(0, et_value)
    et_ordered = ElTree.Element("ordered")
    if obj.ordered is True:
        et_ordered.text = str(1)  # valid xml boolean: (true/false), (1/0)
    else:
        et_ordered.text = str(0)
    return et_submodel_element_collection


def relationship_element_to_xml(obj: model.RelationshipElement) -> ElTree.Element:
    """
    serialization of objects of class RelationshipElement to XML

    :param obj: object of class RelationshipElement
    :return: serialized ELementTree object
    """
    et_relationship_element = ElTree.Element("relationshipElement")
    for i in abstract_classes_to_xml(obj):
        et_relationship_element.insert(0, i)
    et_first = ElTree.Element("first")
    et_ref1 = reference_to_xml(obj.first)
    et_first.insert(0, et_ref1)
    et_relationship_element.insert(0, et_first)

    et_second = ElTree.Element("second")
    et_ref2 = reference_to_xml(obj.second)
    et_second.insert(0, et_ref2)
    et_relationship_element.insert(0, et_second)

    return et_relationship_element


def annotated_relationship_element_to_xml(obj: model.AnnotatedRelationshipElement) -> ElTree.Element:
    """
    serialization of objects of class AnnotatedRelationshipElement to XML

    todo couldn't find it in the schema, so guessing the implementation

    :param obj: object of class AnnotatedRelationshipElement
    :return: serialized ElementTree object
    """
    et_annotated_relationship_element = ElTree.Element("annotatedRelationshipElement")
    for i in abstract_classes_to_xml(obj):
        et_annotated_relationship_element.insert(0, i)
    et_first = ElTree.Element("first")
    et_ref1 = reference_to_xml(obj.first)
    et_first.insert(0, et_ref1)
    et_annotated_relationship_element = update_element(et_annotated_relationship_element, et_first)

    et_second = ElTree.Element("second")
    et_ref2 = reference_to_xml(obj.second)
    et_second.insert(0, et_ref2)
    et_annotated_relationship_element = update_element(et_annotated_relationship_element, et_second)

    if obj.annotation:
        et_annotations = ElTree.Element("annotations")
        for ref in obj.annotation:
            et_reference = reference_to_xml(ref)
            et_annotations.insert(0, et_reference)
        et_annotated_relationship_element.insert(0, et_annotations)

    return et_annotated_relationship_element


def operation_variable_to_xml(obj: model.OperationVariable) -> ElTree.Element:
    """
    serialization of objects of class OperationVariable to XML

    :param obj: object of class OperationVariable
    :return: serialized ElementTree object
    """
    et_operation_variable = ElTree.Element("operationVariable")
    for i in abstract_classes_to_xml(obj):
        et_operation_variable.insert(0, i)
    et_value = ElTree.Element("value")
    et_submodel_element = submodel_element_to_xml(obj.value)
    et_value.insert(0, et_submodel_element)
    et_operation_variable.insert(0, et_value)
    return et_operation_variable


def operation_to_xml(obj: model.Operation) -> ElTree.Element:
    """
    serialization of objects of class Operation to XML

    :param obj: object of class Operation
    :return: serialized ElementTree object
    """
    et_operation = ElTree.Element("operation")
    for i in abstract_classes_to_xml(obj):
        et_operation.insert(0, i)

    et_input_variable = ElTree.Element("inputVariable")
    for input_var in obj.input_variable:
        et_input_var = ElTree.Element("operationVariable")
        et_operation_var = operation_variable_to_xml(input_var)
        et_input_var.insert(0, et_operation_var)
    et_operation.insert(0, et_input_variable)

    et_output_variable = ElTree.Element("outputVariable")
    for output_var in obj.output_variable:
        et_output_var = ElTree.Element("operationVariable")
        et_op_var = operation_variable_to_xml(output_var)
        et_output_var.insert(0, et_op_var)
        et_output_variable.insert(0, et_output_var)
    et_operation.insert(0, et_output_variable)

    et_inout_variable = ElTree.Element("inoutputVariable")
    for inout in obj.in_output_variable:
        et_inout_var = ElTree.Element("operationVariable")
        et_ovar = operation_variable_to_xml(inout)
        et_inout_var.insert(0, et_ovar)
        et_inout_variable.insert(0, et_inout_var)
    et_operation.insert(0, et_inout_variable)

    return et_operation


def capability_to_xml(obj: model.Capability) -> ElTree.Element:
    """
    serialization of objects of class Capability to XML

    todo: doesn't exist this way in the schema, so guessing implementation

    :param obj: object of class Capability
    :return: serialized ElementTree object
    """
    et_capability = ElTree.Element("capability")
    for i in abstract_classes_to_xml(obj):
        et_capability.insert(0, i)
    return et_capability


def entity_to_xml(obj: model.Entity) -> ElTree.Element:
    """
    serialization of objects of class Entity to XML

    :param obj: object of class Entity
    :return: serialized ElementTree object
    """
    et_entity = ElTree.Element("entity")
    for i in abstract_classes_to_xml(obj):
        et_entity.insert(0, i)

    et_statements = ElTree.Element("statements")
    for submodel_element in obj.statement:
        et_submodel_element = submodel_element_to_xml(submodel_element)
        et_statements.insert(0, et_submodel_element)
    et_entity.insert(0, et_statements)

    et_entity_type = ElTree.Element("entityType")
    et_entity_type.text = ENTITY_TYPES[obj.entity_type]
    et_entity.insert(0, et_entity_type)

    if obj.asset:
        et_asset = ElTree.Element("assetRef")
        et_ref = reference_to_xml(obj.asset)
        et_asset.insert(0, et_ref)
        et_entity.insert(0, et_asset)

    return et_entity


def event_to_xml(obj: model.Event) -> ElTree.Element:
    """
    serialization of objects of class Event to XML

    todo didn't find it in the schema, so guessing implementation

    :param obj: object of class Event
    :return: serialized ElementTree object
    """
    et_event = ElTree.Element("event")
    for i in abstract_classes_to_xml(obj):
        et_event.insert(0, i)
    return et_event


def basic_event_to_xml(obj: model.BasicEvent) -> ElTree.Element:
    """
    serialization of objects of class BasicEvent to XML

    :param obj: object of class BasicEvent
    :return: serialized ElementTree object
    """
    et_basic_event = ElTree.Element("basicEvent")
    for i in abstract_classes_to_xml(obj):
        et_basic_event.insert(0, i)
    et_observed = ElTree.Element("observed")
    et_ref = reference_to_xml(obj.observed)
    et_observed.insert(0, et_ref)
    et_basic_event.insert(0, et_observed)
    return et_basic_event
