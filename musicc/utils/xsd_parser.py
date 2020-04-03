# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
#!/usr/bin/env python
# encoding: utf-8
"""
Created by Ben Scott on '25/01/2017'.

Available at https://github.com/benscott/xsdtojson
"""
import simplejson as json
from lxml import etree
from collections import OrderedDict
from distutils.util import strtobool


class XSDParser:

    type_extensions = {}

    type_mappings = {
        "xsd:string": "string",
        "xsd:double": "number",
        "xsd:boolean": "boolean",
        "xsd:int": "integer",
        "xsd:decimal": "number",
        "xsd:dateTime": "datetime-local",
        "xsd:anySimpleType": ["string", "integer", "number", "boolean", "null"],
        "xsd:postitiveInteger": {"type": "integer", "minimum": 0},
    }

    def __init__(self, xsd_src):

        try:
            # Try and read src as XML (will work for requests.content (string)
            self.root = etree.XML(xsd_src)
        except etree.XMLSyntaxError:
            # Or parse the object (will work for files)
            doc = etree.parse(xsd_src)
            self.root = doc.getroot()

        self.namespaces = self.root.nsmap
        self.build_type_extensions()

    def build_type_extensions(self):
        """ Build a list of all enumerator type extensions which can be
        extended by a list of complex type extentions, which are also built,
        which can then be extended the main class 
        For example: 
        - http://www.w3schools.com/xml/el_complextype.asp
        - https://www.w3schools.com/xml/schema_facets.asp
        """
        for simple_type_element in self.root.findall(
            "xsd:simpleType", namespaces=self.namespaces
        ):
            name = simple_type_element.attrib["name"]

            schema = {}
            schema = self.handle_restriction(
                simple_type_element.find("xsd:restriction", namespaces=self.namespaces),
                schema,
            )

            self.type_extensions[name] = schema

        for complex_type_element in self.root.findall(
            "xsd:complexType", namespaces=self.namespaces
        ):
            name = complex_type_element.attrib["name"]

            schema = {}
            self.parse_element_recurse(complex_type_element, schema)
            schema = self.flatten_schema(schema)

            self.type_extensions[name] = schema

    def handle_restriction(self, res_element, schema):
        """
        Takes an "xsd:restriction", determins if it contains enums or not and
        then converts it into an equivelant json type - inlcuding any
        "xsd:enumeration" children it may or may not have too. 
        """
        schema["type"] = self.type_mappings[res_element.get("base")]

        if res_element.findall(".//xsd:enumeration", namespaces=self.namespaces):
            schema["enum"] = []

            for enum in res_element.findall(
                "xsd:enumeration", namespaces=self.namespaces
            ):
                schema["enum"].append(enum.get("value"))

        else:
            for res_child in res_element:
                res_child_name = etree.QName(res_child).localname

                if res_child_name == "minInclusive":
                    schema["minimum"] = res_child.get("value")

                elif res_child_name == "maxInclusive":
                    schema["maximum"] = res_child.get("value")

                elif res_child_name == "minExclusive":
                    schema["minimum"] = res_child.get("value") + 1

                elif res_child_name == "maxExclusive":
                    schema["maximum"] = res_child.get("value") - 1

                elif res_child_name == "maxLength":
                    schema["maxLength"] = res_child.get("value")

                elif res_child_name == "minLength":
                    schema["minLength"] = res_child.get("value")

                elif res_child_name == "length":
                    schema["maxLength"] = res_child.get("value")
                    schema["minLength"] = res_child.get("value")

        return schema

    def parse_element_recurse(self, element, schema):
        """
        Recursively parse elements
        :param element:
        :param schema:
        :return:
        """
        element_name = element.attrib.get("name")
        element_type = element.attrib.get("type")
        element_base = element.attrib.get("base")

        element_max_occurs = element.attrib.get("maxOccurs")
        if element_max_occurs and (
            element_max_occurs == "unbounded" or int(element_max_occurs) > 1
        ):
            schema["array"] = True

        # If element has an extension base, set properties to those of the extension
        if element_base:
            schema.update(self.type_extensions[element_base])
        # If this element has a name, add it to the schema tree
        elif element_name:
            # Create properties dict if it doesn't already exist
            schema.setdefault("properties", OrderedDict())

            # If this element has a type, it needs to be an item in the schema
            # print(element_type, element_name)
            if element_type:
                try:
                    schema["properties"][element_name] = self.type_extensions[
                        element_type
                    ]
                except KeyError:
                    schema["properties"][element_name] = {
                        "type": self.xsd_to_json_schema_type(element_type)
                    }
            # If there's no element type, use it to build the schema tree
            else:
                schema["properties"][element_name] = OrderedDict()
                # Update schema pointer to use the nested element
                # This allows us to build the tree
                schema = schema["properties"][element_name]

        # Does this element have any element descendants?
        # If does, recursively call function
        if element.findall(".//xsd:attribute", namespaces=self.namespaces):
            for child_element in element.getchildren():
                schema["type"] = "object"
                self.parse_element_recurse(child_element, schema)

        # Handle simple types (with restrictions)
        elif element.findall(
            ".//xsd:simpleType//xsd:restriction", namespaces=self.namespaces
        ):
            schema = self.handle_restriction(
                element.find("xsd:simpleType", namespaces=self.namespaces).find(
                    "xsd:restriction", namespaces=self.namespaces
                ),
                schema,
            )

        elif not element_type:
            # We've reached the end of an object tree without finding a type, default it to a string
            schema["type"] = "string"

    @staticmethod
    def flatten_schema(schema):
        """
        If the top level properties dict consists of just one item, and has
        lots of child properties, flatten property dict
        TODO: This is to keep the schema the same as other plugins - is it needed?
        :param schema:
        :return:
        """
        if len(schema["properties"]) == 1:
            first_property = next(iter(schema["properties"]))
            # If the sole top level item has child properties, then flatten
            # If there's no child properties, do no flatten
            if "properties" in schema["properties"][first_property]:
                schema = schema["properties"][first_property]
        return schema

    def json_schema(self):
        """
        Main entry point - convert the XSD file to
        :return:
        """
        schema = OrderedDict()
        # Starting point: all elements in the root of the document
        # This allows us to exclude complexType used as named types (e.g. tests/person.xsd)
        for element in self.root.findall("xsd:element", namespaces=self.namespaces):
            self.parse_element_recurse(element, schema)

        # Flatten the schema - so if there's just one element at the root, this is removed
        schema = self.flatten_schema(schema)
        # Set schema
        return json.dumps(schema, sort_keys=False, indent=4)

    def xsd_to_json_schema_type(self, element_type):
        try:
            return self.type_mappings[element_type]
        except KeyError:
            return "string"
