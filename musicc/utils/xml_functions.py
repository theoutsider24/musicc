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
## @package xml_functions
#  This module contains xml-xsd validation tools for use in the MUSICC project<br>

import os
import sys
import argparse

from contextlib import contextmanager
from lxml import etree
from io import StringIO, BytesIO
from musicc.utils.tools import working_directory, information, warning

from xmljson import badgerfish as bf

import zipfile
import tempfile
import shutil

import logging

logger = logging.getLogger("musicc")

##
#  Loads a schemda file (.xsd) from a zip file. If successful, returns a schema structure.
#  If not an exception is raised. The caller can catch an etree.XMLSyntaxError exception
#  if it is raised and retrieve the list of errors that caused it. Otherwise, the
#  another exception will have to be handled by the caller.
#  @param xsd_path path/name of xsd master file to be loaded
#  @param zip_file zipfile.ZipFile object containing the master xsd file and files it references (include/import)
#  @rtype: lxml.etree.XMLSchema
#  @return: Schema structure
#  @rtype: exception: lxml.etree.XMLSchemaParseError
#  @return: List of syntax errors (list in err.error_log)
#  @details Example of use showing how to use it and extract information
#
#  @code
#  try:
#       schema = load_xsd_file("a_file.xsd", zipfile)
#   except lxml.etree.XMLSchemaParseError as err:
#       for e in err.error_log:
#           print("line:", e.line, "column:", "error message:", e.message)
#   except:
#       ..... handle other errors
#  @endcode
#


def load_xsd_zip(xsd_path: str, zip_file: zipfile.ZipFile) -> etree.XMLSchema:

    with tempfile.TemporaryDirectory() as tmpdirname:
        with working_directory(tmpdirname):
            zip_file.extractall(path=tmpdirname)
            try:
                xsd_doc = load_xsd_file(xsd_path)
                return xsd_doc

            except Exception as e:
                logger.info(
                    "Error: {0}, loading: {1} from {2}, zipfile namelist:{3}".format(
                        e, xsd_path, zip_file, zip_file.namelist()
                    )
                )
                # zip_file.printdir() can also be used or:
                # for root, directories, filenames in os.walk('.'):
                #     for directory in directories:
                #         print (os.path.join(root, directory) )
                #     for filename in filenames:
                #         print (os.path.join(root,filename) )
                raise e


##
#  Loads a schemda file (.xsd). If successful, returns a schema structure.
#  If not an exception is raised. The caller can catch an etree.XMLSyntaxError exception
#  if it is raised and retrieve the list of errors that caused it. Otherwise, the
#  another exception will have to be handled by the caller.
#  @param xsd_path path/name of xsd file to be loaded
#  @rtype: lxml.etree.XMLSchema
#  @return: Schema structure
#  @rtype: exception: lxml.etree.XMLSchemaParseError
#  @return: List of syntax errors (list in err.error_log)
#  @details Example of use showing how to use it and extract information
#
#  @code
#  try:
#       schema = load_xsd_file("a_file.xsd")
#   except lxml.etree.XMLSchemaParseError as err:
#       for e in err.error_log:
#           print("line:", e.line, "column:", "error message:", e.message)
#   except:
#       ..... handle other errors
#  @endcode
#


def load_xsd_file(xsd_path: str) -> etree.XMLSchema:

    filename_xsd = xsd_path.strip()
    basename_xsd = os.path.basename(filename_xsd)
    dirname_xsd = os.path.abspath(os.path.dirname(filename_xsd))

    try:
        # open and read schema file
        with working_directory(dirname_xsd):
            with open(basename_xsd, "rb") as schema_file:
                schema_to_check = schema_file.read()

    except Exception as e:
        logger.warning("Exception: {0}, loading: {1}".format(e, xsd_path))
        raise e

    # Unfortunately .... as xsd schemas can include other schema, the generation of the internal schema representation
    # requires a file system not only of the schema files but also of the included schema files. So, a temporary
    # change of context so that the working directory is that of the top level schema file's location is required
    with working_directory(dirname_xsd):
        try:
            xmlschema_doc = etree.parse(BytesIO(schema_to_check))
            xmlschema = etree.XMLSchema(xmlschema_doc)
            return xmlschema

        except Exception as e:
            logger.warning("Unexpected exception: {0} loading: {1}".format(e, xsd_path))
            raise e


##
#  Loads a xml file (.xml). If successful, returns an xml structure.
#  as an Error list in the form of an etree.XMLSyntaxError structure or None
#  If not an exception is raised. The caller can catch an etree.XMLSyntaxError exception
#  if it is raised and retrieve the list of errors that caused it. Otherwise, the
#  another exception will have to be handled by the caller.
#  @param xml_path path/name of xml file to be loaded
#  @rtype: lxml.etree._ElementTree
#  @return: XML structure
#  @rtype: exception: lxml.etree.XMLSyntaxError
#  @return: List of syntax errors (list in err.error_log)
#  @details Example of use showing how to use it and extract information
#
#  @code
#  try:
#       xml = load_xml_file("a_file.xml")
#   except lxml.etree.XMLSyntaxError as err:
#       for e in err.error_log:
#           print("line:", e.line, "column:", "error message:", e.message)
#   except:
#        ..... handle other errors
#  @endcode
#
def load_xml_file(xml_path: str) -> etree._ElementTree:

    filename_xml = xml_path.strip()
    basename_xml = os.path.basename(filename_xml)
    dirname_xml = os.path.abspath(os.path.dirname(filename_xml))

    # open and read xml file
    try:
        with working_directory(dirname_xml):
            with open(basename_xml, "rb") as xml_file:
                xml_to_check = xml_file.read()

    except Exception as e:
        logger.warning("Unexpected exception: {0} loading: {1}".format(e, xml_path))
        raise e

    # parse xml
    try:
        xml_doc = etree.parse(BytesIO(xml_to_check))
        return xml_doc

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        logger.warning(
            "XMLSyntaxError(s): {0} parsing: {1}".format(str(err.error_log), xml_path)
        )
        raise err

    except Exception as e:
        logger.warning("Exception caught: {0}, loading: {1}".format(e, xml_path))
        raise e


##
#  Validates a xml file (.xml) against a schema (.xsd). If successful, returns None.
#  If not successful due to a contents (etree.DocumentInvalid exception)then returns
#  the a list of validation failure in the form of a sand an xml structure.
#  as an Error list in the form of an etree.XMLSyntaxError structure.
#  Otherwise, an exception is raised that the caller should handle.

#  @param xml_doc xml document to be validated
#  @param xsd_doc xsd document for the xml document to be validated against
#  @return: List of syntax errors (list in err.error_log)
#  @details Example of use showing how to use it and extract information
#
#  @code
#  try:
#       error_log = check_validation_errors("a_file.xml", "a_file.xsd")
#       if (error_log):
#       for e in error_log:
#           print("line:", e.line, "column:", "error message:", e.message)
#   except:
#        ..... handle other errors
#  @endcode
#
def check_validation_errors(xml_doc, xsd_doc) -> etree.XMLSyntaxError:

    # The assumption is that the xml and xsd are well formatted documents!
    # Including another pre-processing scan here is feasible

    # validate against schema
    try:
        xsd_doc.assertValid(xml_doc)
        return None

    except etree.DocumentInvalid as err:
        raise err

    except Exception as e:
        logger.warning(
            "Exception caught: {0}, validating: {1} against: {2}".format(
                e, xml_doc, xsd_doc
            )
        )
        raise e

## Convert an xml string to a python dict
#  @param xml_string An xml string
#  @return A python dict
def convert_xml_to_json(xml_string):
    # Convert xml string > lxml etree > BadgerFish python dict
    return bf.data(etree.fromstring(xml_string))

## Create a schema from a Revision object or file data, either as an XSD file or zip file
#  @param model A Revision model or file data
#  @param root_type [Optional]The root type to search for when searching zips
#  @return The schema object
def load_xsd_from_blob(model, root_type=None):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        if hasattr(model, 'revision_xsd'):
            temp_file.write(model.revision_xsd)
        else:
            temp_file.write(model)
        if not zipfile.is_zipfile(temp_file):
            temp_file.close()
            schema = load_xsd_file(temp_file.name)
        else:
            with zipfile.ZipFile(temp_file) as zip_file:
                file_name = find_base_xsd_file(zip_file, root_type)
                schema = load_xsd_zip(file_name, zip_file)
                temp_file.close()
        os.unlink(temp_file.name)
        return schema

## Get the name of the root XSD in a zip of XSDs
#  @param zip_file A ZipFile to search
#  @param root_type The root node to search for
#  @return The name of the discovered file
def find_base_xsd_file(zip_file, root_type):
    zip_contents = {name: zip_file.read(name) for name in zip_file.namelist()}

    filenames = []
    for filename, file in zip_contents.items():
        xml = etree.fromstring(file)
        root_name = xml.xpath(
            "xsd:element/@name", namespaces={"xsd": "http://www.w3.org/2001/XMLSchema"}
        )
        if len(root_name) > 0 and root_name[0] == root_type:
            filenames.append(filename)

    if len(filenames) == 0:
        raise Exception("More than one root xsd file in zip")
    elif len(filenames) > 1:
        raise Exception("No root xsd file in zip")
    else:
        return filenames[0]


def validate_xml_against_xsd(xml_blob, schema):
    xml = etree.fromstring(xml_blob)
    check_validation_errors(xml, schema)

def replace_value_in_xml(xml_root, tag_name, attribute_name, value):
    elements_changed = [
        element.set(attribute_name, value)
        for element in xml_root.xpath("//" + tag_name)
    ]

    if not elements_changed:
        raise Exception("{0} not found for {1}".format(attribute_name, tag_name))