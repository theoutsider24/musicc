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
import unittest
import os

from musicc.utils.tools import working_directory, information, warning
from musicc.utils.xml_functions import (
    load_xsd_file,
    load_xsd_zip,
    load_xml_file,
    check_validation_errors,
)

from lxml import etree
import zipfile
from musicc.tests.test_url_requests import UploadZipTestCase
from musicc.models.BaseModel import BaseModel
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from django.conf import settings
from musicc.models.OpenScenario import OpenScenario


################### XSD ####################################################


class XSDTestCase(unittest.TestCase):
    def check_xsd(self, xsd_file):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            self.assertIsNotNone(load_xsd_file(xsd_file))

    def exception_xsd(self, e, xsd_file):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            self.assertRaises(e, load_xsd_file, xsd_file)


class TestXSDChecker(XSDTestCase):
    def test_ship_xsd_ok(self):
        self.check_xsd("test_files/shiporder_basic.xsd")

    def test_no_xsd(self):
        self.exception_xsd(FileNotFoundError, "does_not_exist.xsd")

    def test_badly_formatted_xsd_file(self):
        self.exception_xsd(
            etree.XMLSchemaParseError,
            "test_files/shiporder_format_error_basic.xsd",
        )


###################### XML #################################################


class XMLTestCase(unittest.TestCase):
    def check_xml(self, xml_file):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            self.assertIsNotNone(load_xml_file(xml_file))

    def exception_xml(self, e, xml_file):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            self.assertRaises(e, load_xml_file, xml_file)


class TestXMLChecker(XMLTestCase):
    def test_ship_xml_ok(self):
        self.check_xml("test_files/shiporder_basic.xsd")

    def test_no_xml(self):
        self.exception_xml(FileNotFoundError, "does_not_exist.xml")

    def test_badly_formatted_xml_file(self):
        self.exception_xml(
            etree.XMLSyntaxError, "test_files/test_format_error_shiporder.xml"
        )


###################### XML + XSD ######################################


class ValidationTestCase(unittest.TestCase):
    def check_if_valid(self, xml_file, xsd_file) -> (etree.XMLSyntaxError):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            xsd_doc = load_xsd_file(xsd_file)
            xml_doc = load_xml_file(xml_file)
            try:
                return check_validation_errors(xml_doc, xsd_doc)
            except etree.DocumentInvalid as err: 
                return err.error_log
            
            

    def exception_during_validation(self, e, xml_file, xsd_file):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            xsd_doc = load_xsd_file(xsd_file)
            xml_doc = load_xml_file(xml_file)
            self.assertRaises(e, check_validation_errors, xml_doc, xsd_doc)



class TestScenarioValidation(UploadZipTestCase):
    def test_base_model_parameter_declaration_validation(self):
        with open(os.path.join(settings.BASE_DIR, "tests", "test_files", "oncoming.xosc"), "rb") as xosc_file:
            self.assertRaises(etree.DocumentInvalid, BaseModel.validate, OpenScenarioRevision.latest_revision(), xosc_file.read(), "OpenSCENARIO")


    def test_open_scenario_parameter_declaration_validation(self):
        with open(os.path.join(settings.BASE_DIR, "tests", "test_files", "oncoming.xosc"), "rb") as xosc_file:
            try:
                OpenScenario.validate(OpenScenarioRevision.latest_revision(), xosc_file.read(), "OpenSCENARIO")
            except etree.DocumentInvalid as err:
                self.assertEqual(len(err.error_log), 1)
                self.assertNotEqual(err.error_log[0].message, "Element 'Absolute', attribute 'value': '$InitialSpeed' is not a valid value of the atomic type 'xs:double'.")

class TestValidationChecker(ValidationTestCase):
    def test_ship_ok(self):
        self.assertIsNone(
            self.check_if_valid(
                "test_files/test_shiporder.xml", "test_files/shiporder_basic.xsd"
            )
        )

    def test_scenario_Overtaker_ok(self):
        self.assertIsNone(
            self.check_if_valid(
                "test_files/OpenSCENARIO_v0.9.1/Examples/Standard/Overtaker/Overtaker.xosc",
                "test_files/OpenSCENARIO_v0.9.1/OpenSCENARIO_v0.9.1.xsd",
            )
        )

    def test_ship_fail(self):
        self.assertIsNotNone(
            self.check_if_valid(
                "test_files/test_fail_shiporder.xml", "test_files/shiporder_basic.xsd"
            )
        )

    def test_error_messages(self):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            xsd_doc = load_xsd_file("test_files/shiporder_basic.xsd")
            xml_doc = load_xml_file("test_files/test_fail_shiporder.xml")
            try:
                error_log = check_validation_errors(xml_doc, xsd_doc)
            except etree.DocumentInvalid as err: 
                error_log = err.error_log

            self.assertIsNotNone(error_log)
            self.assertEqual(len(error_log), 2, "2 errors should be detected")
            self.assertEqual(
                error_log[0].domain_name, "SCHEMASV", "domain name should be SCHEMASV"
            )
            self.assertEqual(
                error_log[0].path, "/shiporder/shipto/city", "path incorrect"
            )
            self.assertEqual(error_log[0].column, 0, "incorrect column reported")
            self.assertEqual(error_log[0].line, 10, "incorrect line reported")

    def test_validate_from_zip_simple(self):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            zip_file = zipfile.ZipFile("test_files/shiporder_basic.zip", mode="r")
            xsd_doc = load_xsd_zip("shiporder_basic.xsd", zip_file)
            xml_doc = load_xml_file("test_files/test_shiporder.xml")
            error_log = check_validation_errors(xml_doc, xsd_doc)

            self.assertIsNone(error_log)

    def test_validate_from_zip_complex(self):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            zip_file = zipfile.ZipFile(
                "test_files/OpenSCENARIO_v0.9.1/OpenSCENARIO_v0.9.1.zip", mode="r"
            )
            xml_doc = load_xml_file(
                "test_files/OpenSCENARIO_v0.9.1/Examples/Standard/Overtaker/Overtaker.xosc"
            )
            xsd_doc = load_xsd_zip("OpenSCENARIO_v0.9.1.xsd", zip_file)
            error_log = check_validation_errors(xml_doc, xsd_doc)

            self.assertIsNone(error_log)

    def test_validate_from_zip_wrong_xsd_master(self):
        with working_directory(os.path.abspath(os.path.dirname(__file__))):
            zip_file = zipfile.ZipFile("test_files/shiporder_basic.zip", mode="r")
            self.assertRaises(
                FileNotFoundError, load_xsd_zip, "wrong_xsd_master.xsd", zip_file
            )


#######################################################################

if __name__ == "__main__":
    unittest.main()
