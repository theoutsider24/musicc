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
import re, os
from musicc.utils.queries import QueryParser
from django.test import TestCase, Client
from musicc.models.MusiccScenario import MusiccScenario
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.OpenScenario import OpenScenario
from musicc.models.ScenarioImage import ScenarioImage
from musicc.models.OpenDrive import OpenDrive
from musicc.models.QueryCache import QueryCache
from musicc.models.logs.DownloadLog import DownloadLog
from musicc.models.System import System
from django.conf import settings
import zipfile
from musicc.tests.utilities import (
    initialise_revision_tables_via_url,
    initialise_scenario_tables,
    initialise_super_user,
    create_outdated_scenarios_via_url,
    set_media_root,
    clear_media_root,
    revision_info_list
)
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.ZipSummary import ZipSummary
from io import BytesIO
import lxml
import django.http.response as django_response
import json


class UploadZipTestCase(TestCase):
    def setUp(self):
        set_media_root()
        initialise_super_user()
        login = self.client.login(username="admin", password="password")
        self.assertTrue(login)
        User = get_user_model()
        current_user = User.objects.get(id=self.client.session["_auth_user_id"])

        System.register_as_master()
        initialise_revision_tables_via_url(self.client, current_user)
        self.test_data_revision_folder = os.path.join(settings.BASE_DIR, "tests", "test_files", "Test Data", "0.1.2")

    def tearDown(self):
        clear_media_root()
        
    def upload_zip(self, path):
        with open(
            path,
            "rb",
        ) as zip_file:
            response = self.client.post(
                "http://localhost:8000/upload_zip", {"file_ingestion_zip": zip_file}
            )
            self.assertEqual(
                response.status_code, django_response.HttpResponseBase.status_code
            )
            self.assertEqual(response.content, b"Zip uploaded succesfully")

    def upload_zip_wrong_file_type(self):
        with open(
            os.path.join(
                settings.BASE_DIR, "tests", "test_files", "test_shiporder.xml"
            ),
            "rb",
        ) as zip_file:
            response = self.client.post(
                "http://localhost:8000/upload_zip", {"file_ingestion_zip": zip_file}
            )
            self.assertEqual(
                response.status_code,
                django_response.HttpResponseServerError.status_code,
            )
            self.assertEqual(response.content, b"Uploaded file not a zip-file")

    def upload_zip_missing_osc_file(self, path):
        with open(
            path,
            "rb",
        ) as zip_file:
            response = self.client.post(
                "http://localhost:8000/upload_zip", {"file_ingestion_zip": zip_file}
            )
            
            error_json = json.loads(response.content)
            for key,value in error_json["errors"].items():
                response_string_match = re.match(r"Cannot find file (.*)\.xosc", value[0])
                self.assertIsNotNone(response_string_match)

            self.assertEqual(
                response.status_code,
                django_response.HttpResponseServerError.status_code,
            )

    def check_model_counts(
        self,
        desired_scenario_count,
        desired_open_drive_count,
        desired_open_scenario_count,
    ):
        scenario_count = MusiccScenario.objects.count()
        open_scenario_count = OpenScenario.objects.count()
        open_drive_count = OpenDrive.objects.count()
        self.assertEqual(scenario_count, desired_scenario_count)
        self.assertEqual(open_scenario_count, desired_open_scenario_count)
        self.assertEqual(open_drive_count, desired_open_drive_count)


class QueryURLTestCase(TestCase):
    def setUp(self):
        set_media_root()
        initialise_super_user()
        login = self.client.login(username="admin", password="password")
        self.assertTrue(login)
        User = get_user_model()
        current_user = User.objects.get(id=self.client.session["_auth_user_id"])

        System.register_as_master()
        create_outdated_scenarios_via_url(self.client, current_user)
        initialise_revision_tables_via_url(self.client, current_user)
        initialise_scenario_tables(current_user)

    def tearDown(self):
        clear_media_root()

    def check_query_returns_correct_count(self, query, expected_return_count):
        response = self.client.get("http://localhost:8000/query", {"query": query})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recordsFiltered"], expected_return_count)
        self.assertIsNotNone(response.json()["estimatedDownloadSize"], response.json())
        self.assertIsNotNone(response.json()["results"])
        self.assertEqual(len(response.json()["results"]), expected_return_count)


class TestZipUpload(UploadZipTestCase):
    def test_upload_zip(self):
        self.check_model_counts(0, 0, 0)

        self.upload_zip(os.path.join(self.test_data_revision_folder, "master_scenarios.zip"))

        self.check_model_counts(2, 1, 2)

    def test_upload_zip_error(self):
        self.check_model_counts(0, 0, 0)

        self.upload_zip_wrong_file_type()

        self.check_model_counts(0, 0, 0)

    def test_zip_missing_file(self):

        self.check_model_counts(0, 0, 0)

        self.upload_zip_missing_osc_file(os.path.join(self.test_data_revision_folder, "test_scenarios_missing_xosc.zip"))

        self.check_model_counts(1, 1, 1)

    def test_zip_with_images(self):
        # Check number of images uploaded is 0
        self.assertEqual(0, ScenarioImage.objects.count())

        self.upload_zip(os.path.join(self.test_data_revision_folder, "master_scenarios.zip"))

        self.assertEqual(3, ScenarioImage.objects.count())

    def test_zip_with_more_images(self):
        self.assertEqual(0, ScenarioImage.objects.count())

        #Zip contains 4 images, 1 of which should not match any filename within the zip, meaning it isn't uploaded.
        self.upload_zip(os.path.join(self.test_data_revision_folder,  "test_scenarios_extra_image.zip"))

        self.assertEqual(3, ScenarioImage.objects.count())

    def test_zip_none_image(self):
        self.assertEqual(0, ScenarioImage.objects.count())

        self.upload_zip(os.path.join(self.test_data_revision_folder, "test_scenarios_random_image.zip"))

        self.assertEqual(3, ScenarioImage.objects.count())

    def test_zip_summary(self):
        with open(
            os.path.join(os.path.join(self.test_data_revision_folder,  "master_scenarios.zip")),
            "rb",
        ) as zip_file:
            uploaded_file = UploadedFile(file=zip_file, name="master_scenarios.zip")
            zip_summary = ZipSummary(uploaded_file)

            self.assertEqual(len(zip_summary.musicc_list), 2)
            self.assertEqual(len(zip_summary.open_drive_list), 1)
            self.assertEqual(len(zip_summary.open_scenario_list), 2)

            self.assertEqual(zip_summary.catalog_tuple_list[0][0], "EmergencyStop.xosc")
            self.assertEqual(
                zip_summary.catalog_tuple_list[0][1], "Catalogs/Maneuver"
            )


class TestQueryURL(QueryURLTestCase):
    positive_queries = [
        "CountryCode = 'gb'",
        "CountryCode = gb",
        'CountryCode = "gb"',
        "CountryCode = 'GB'",
        "CountryCode = GB",
        'CountryCode = "GB"',
        "CountryCode contains g",
        "CountryCode CONTAINS g",
        "CountryCode CONTAINS 'g'",
        "CountryCode CONTAINS 'G'",
        "CountryCode CONTAINS 'G' and CountryCode CONTAINS 'B'",
        "(CountryCode CONTAINS 'G') and (CountryCode CONTAINS 'B')",
    ]

    negative_queries = [
        "CountryCode != 'gb'",
        "CountryCode != gb",
        'CountryCode != "gb"',
        "NOT CountryCode = 'GB'",
        "not CountryCode = GB",
        'NoT CountryCode = "GB"',
        "CountryCode contains f",
        "NOT CountryCode CONTAINS g",
    ]

    def test_search_page_request(self):
        response = self.client.get("http://localhost:8000/search")
        self.assertEqual(
            response.status_code, django_response.HttpResponseBase.status_code
        )

    def test_basic_queries(self):
        for query in self.positive_queries:
            self.check_query_returns_correct_count(query, 2)

        for query in self.negative_queries:
            self.check_query_returns_correct_count(query, 0)

        total_scripted_test_cases = len(self.positive_queries) + len(
            self.negative_queries
        )
        self.assertEqual(QueryCache.objects.count(), total_scripted_test_cases)
        self.check_query_returns_correct_count("CountryCode != unique", 2)
        self.assertEqual(QueryCache.objects.count(), total_scripted_test_cases + 1)
        self.check_query_returns_correct_count("CountryCode != unique", 2)
        self.assertEqual(QueryCache.objects.count(), total_scripted_test_cases + 1)

    def test_invalid_query(self):
        query = "CountryCode = = 'GB'"
        response = self.client.get("http://localhost:8000/query", {"query": query})
        self.assertEqual(
            response.status_code, django_response.HttpResponseBadRequest.status_code
        )

    def perform_standard_query(self):
        query = "CountryCode = 'GB'"
        response = self.client.get("http://localhost:8000/query", {"query": query})
        self.assertEqual(response.json()["recordsFiltered"], 2)

        query_id = response.json()["query_id"]
        self.assertTrue(QueryCache.objects.filter(pk=query_id).exists())
        return query_id

    def test_query_is_downloadable(self):
        query_id = self.perform_standard_query()

        query_file = self.client.get(
            "http://localhost:8000/download", {"query_id": query_id}
        )

        zip_file = zipfile.ZipFile(BytesIO(query_file.getvalue()))
        zip_contents = zip_file.namelist()

        has_xmus = any(zip_element.endswith(".xmus") for zip_element in zip_contents)
        has_xodr = any(zip_element.endswith(".xodr") for zip_element in zip_contents)
        has_xosc = any(zip_element.endswith(".xosc") for zip_element in zip_contents)

        self.assertTrue(has_xmus)
        self.assertTrue(has_xodr)
        self.assertTrue(has_xosc)

        open_scenario_file_name = next(
            zip_element
            for zip_element in zip_contents
            if (zip_element.endswith(".xosc") and not "Catalogs" in zip_element)
        )
        open_scenario_file = zip_file.open(open_scenario_file_name)
        open_scenario_file_blob = bytes(open_scenario_file.read())
        open_scenario = lxml.etree.fromstring(open_scenario_file_blob)

        # Native download should not have added a comment to the ODR file
        self.assertFalse(open_scenario[0].tag is lxml.etree.Comment)

    def test_query_is_downloadable_non_native(self):
        query_id = self.perform_standard_query()

        query_file = self.client.get(
            "http://localhost:8000/download", {"query_id": query_id, "native": False}
        )

        zip_file = zipfile.ZipFile(BytesIO(query_file.getvalue()))
        zip_contents = zip_file.namelist()

        xmus_count = [
            zip_element.endswith(".xmus") for zip_element in zip_contents
        ].count(True)
        xodr_count = [
            zip_element.endswith(".xodr") for zip_element in zip_contents
        ].count(True)
        xosc_count = [
            zip_element.endswith(".xosc")
            for zip_element in zip_contents
            if not "Catalogs" in zip_element
        ].count(True)

        self.assertEqual(xmus_count, 0)
        self.assertEqual(xodr_count, 2)
        self.assertEqual(xosc_count, 2)

        open_scenario_file_name = next(
            zip_element
            for zip_element in zip_contents
            if (zip_element.endswith(".xosc") and not "Catalogs" in zip_element)
        )
        open_scenario_file = zip_file.open(open_scenario_file_name)
        open_scenario = lxml.etree.fromstring(open_scenario_file.read())

        open_drive_file_name = next(
            zip_element for zip_element in zip_contents if zip_element.endswith(".xodr")
        ).split("/")[-1]

        # Non-native download should contain two comments
        self.assertTrue(open_scenario[0].tag is lxml.etree.Comment)
        self.assertTrue(open_scenario[1].tag is lxml.etree.Comment)
        self.assertTrue(open_scenario[2].tag is lxml.etree.Comment)

        # The first comment should contain the id of the musicc record
        musicc_record = QueryCache.objects.get(pk=query_id).results.all()[0]
        musicc_id = musicc_record.get_human_readable_id()
        self.assertTrue(str(musicc_id) in open_scenario[0].text)

        # The second comment should contain the metadata from the musicc record
        musicc_metadata = lxml.etree.fromstring(bytes(musicc_record.musicc_blob)).find(
            "Metadata"
        )

        self.assertEqual(
            open_drive_file_name,
            open_scenario.find("RoadNetwork").find("Logics").get("filepath"),
        )

        musicc_metadata_string = lxml.etree.tostring(
            musicc_metadata, encoding="utf-8"
        ).decode("utf-8")
        self.assertXMLEqual(
            open_scenario[2].text.replace("##", "--"), musicc_metadata_string
        )

    def test_download_is_reproducible(self):
        query_id = self.perform_standard_query()

        original_query_file = self.client.get(
            "http://localhost:8000/download", {"query_id": query_id, "native": False}
        )
        zip_file = zipfile.ZipFile(BytesIO(original_query_file.getvalue()))

        zip_contents = zip_file.namelist()
        open_scenario_file_name = next(
            zip_element
            for zip_element in zip_contents
            if (zip_element.endswith(".xosc") and not "Catalogs" in zip_element)
        )
        open_scenario_file = zip_file.open(open_scenario_file_name)
        open_scenario = lxml.etree.fromstring(open_scenario_file.read())
        original_first_parameter_value = open_scenario.find("ParameterDeclaration")[
            0
        ].get("value")

        download_id = DownloadLog.objects.latest("id").id

        for _ in range(3):
            query_file = self.client.get(
                "http://localhost:8000/download",
                {
                    "query_id": query_id,
                    "native": False,
                    "previous_download_id": download_id,
                },
            )
            zip_file = zipfile.ZipFile(BytesIO(query_file.getvalue()))

            zip_contents = zip_file.namelist()
            open_scenario_file_name = next(
                zip_element
                for zip_element in zip_contents
                if (zip_element.endswith(".xosc") and not "Catalogs" in zip_element)
            )
            open_scenario_file = zip_file.open(open_scenario_file_name)
            open_scenario = lxml.etree.fromstring(open_scenario_file.read())
            first_parameter_value = open_scenario.find("ParameterDeclaration")[0].get(
                "value"
            )
            self.assertEquals(first_parameter_value, original_first_parameter_value)

    def test_download_is_randomised(self):
        query_id = self.perform_standard_query()

        results_found = []
        for _ in range(10):
            query_file = self.client.get(
                "http://localhost:8000/download",
                {"query_id": query_id, "native": False},
            )

            zip_file = zipfile.ZipFile(BytesIO(query_file.getvalue()))

            zip_contents = zip_file.namelist()
            open_scenario_file_name = next(
                zip_element
                for zip_element in zip_contents
                if (zip_element.endswith(".xosc") and not "Catalogs" in zip_element)
            )
            open_scenario_file = zip_file.open(open_scenario_file_name)
            open_scenario = lxml.etree.fromstring(open_scenario_file.read())
            first_parameter_value = open_scenario.find("ParameterDeclaration")[0].get(
                "value"
            )
            results_found.append(first_parameter_value)
        self.assertIsNot(len(set(results_found)), 1)
        self.assertIsNot(len(set(results_found)), 0)

    def test_invalid_query_download(self):
        query_id = 999

        response = self.client.get(
            "http://localhost:8000/download", {"query_id": query_id}
        )

        self.assertEqual(
            response.status_code, django_response.HttpResponseServerError.status_code
        )

    def test_invalid_repeated_download(self):
        query_id = self.perform_standard_query()

        response = self.client.get(
            "http://localhost:8000/download", {"query_id": query_id}
        )

        download_id = DownloadLog.objects.latest("id").id

        response = self.client.get(
            "http://localhost:8000/download",
            {"query_id": query_id, "previous_download_id": download_id + 1},
        )
        self.assertEqual(
            response.status_code, django_response.HttpResponseServerError.status_code
        )

    def test_get_metadata(self):
        response = self.client.get("http://localhost:8000/get_metadata_fields")

        schema = json.loads(response.content)
        self.assertEquals(schema["type"], "object")
        self.assertIsNot(len(schema["properties"]), 0)

    def test_get_metadata_for_named_revision(self):
        response = self.client.get(
            "http://localhost:8000/get_metadata_fields", {"revision": "0.1.2"}
        )

        schema = json.loads(response.content)
        self.assertEquals(schema["type"], "object")
        self.assertIsNot(len(schema["properties"]), 0)

    def test_get_metadata_for_non_existent_named_revision(self):
        response = self.client.get(
            "http://localhost:8000/get_metadata_fields", {"revision": "bla"}
        )

        self.assertEqual(
            response.status_code, django_response.HttpResponseNotFound.status_code
        )

    def test_query_order_by_ascending_MUSICC_ID(self):
        
        response = self.client.get(
            "http://localhost:8000/query", {"order_column": "metadata__MUSICC_ID", "order_direction": "asc"}
        )
        musicc_id_1 = response.json()['results'][0]['metadata']['MUSICC_ID']
        musicc_id_2 = response.json()['results'][1]['metadata']['MUSICC_ID']
        musicc_id_1_int = int(musicc_id_1.replace('M',''))
        musicc_id_2_int = int(musicc_id_2.replace('M',''))
        
        self.assertTrue(
            musicc_id_1_int<musicc_id_2_int
        )

    def test_query_order_by_descending_MUSICC_ID(self):
        
        response = self.client.get(
            "http://localhost:8000/query", {"order_column": "metadata__MUSICC_ID", "order_direction": "desc"}
        )
        musicc_id_1 = response.json()['results'][0]['metadata']['MUSICC_ID']
        musicc_id_2 = response.json()['results'][1]['metadata']['MUSICC_ID']
        musicc_id_1_int = int(musicc_id_1.replace('M',''))
        musicc_id_2_int = int(musicc_id_2.replace('M',''))
        
        self.assertTrue(
            musicc_id_1_int>musicc_id_2_int
        )


if __name__ == "__main__":
    unittest.main()
