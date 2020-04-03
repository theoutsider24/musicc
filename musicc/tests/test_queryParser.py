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
import re, os
from musicc.utils.queries import QueryParser
from django.test import TestCase, client
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from musicc.models.revisions.OpenDriveRevision import OpenDriveRevision
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.System import System
from django.contrib.auth import get_user_model
from musicc.tests.utilities import (
    initialise_revision_tables_via_url,
    initialise_scenario_tables,
    initialise_super_user,
    create_outdated_scenarios_via_url,
    set_media_root,
    clear_media_root,
    revision_info_list
)
from musicc.models.OpenDrive import OpenDrive
from musicc.models.OpenScenario import OpenScenario
from musicc.models.MusiccScenario import MusiccScenario


class QueryTestCase(TestCase):
    def setUp(self):
        set_media_root()
        initialise_super_user()
        login = self.client.login(username="admin", password="password")
        self.assertTrue(login)
        User = get_user_model()
        self.current_user = User.objects.get(id=self.client.session["_auth_user_id"])

        System.register_as_master()
        create_outdated_scenarios_via_url(self.client, self.current_user)
        initialise_revision_tables_via_url(self.client, self.current_user)
        initialise_scenario_tables(self.current_user)

    def tearDown(self):
        clear_media_root()

    def check_query_matches_standard_result(self, query, filter_dict):
        qs1 = MusiccScenario.objects.filter(**filter_dict)
        qs2 = MusiccScenario.objects.filter(QueryParser(query).evaluate(self.current_user))
        self.assertQuerysetEqual(qs1, [repr(r) for r in qs2])

    def check_query_matches_standard_result_negated(self, query, filter_dict):
        qs1 = MusiccScenario.objects.filter(**filter_dict)
        qs2 = MusiccScenario.objects.exclude(QueryParser(query).evaluate(self.current_user))
        self.assertQuerysetEqual(qs1, [repr(r) for r in qs2])


class TestQueryParser(QueryTestCase):
    def test_queries_numbers(self):
        self.check_query_matches_standard_result(
            query="InitialSpeedLimit > 1",
            filter_dict={"metadata__InitialSpeedLimit__gt": 1},
        )

        self.check_query_matches_standard_result(
            query="InitialSpeedLimit < 1",
            filter_dict={"metadata__InitialSpeedLimit__lt": 1},
        )

        self.check_query_matches_standard_result_negated(
            query="NOT InitialSpeedLimit > 1",
            filter_dict={"metadata__InitialSpeedLimit__gt": 1},
        )

        self.check_query_matches_standard_result(
            query="InitialSpeedLimit = 1",
            filter_dict={"metadata__InitialSpeedLimit": 1},
        )

        self.check_query_matches_standard_result_negated(
            query="InitialSpeedLimit != 1",
            filter_dict={"metadata__InitialSpeedLimit": 1},
        )

        self.check_query_matches_standard_result(
            query="InitialSpeedLimit == 1",
            filter_dict={"metadata__InitialSpeedLimit": 1},
        )

    def test_queries_strings(self):
        self.check_query_matches_standard_result(
            query="CountryCode = 'GB'",
            filter_dict={"metadata__CountryCode__iexact": "GB"},
        )

        self.check_query_matches_standard_result(
            query="CountryCode = 'gb'",
            filter_dict={"metadata__CountryCode__iexact": "gb"},
        )

        self.check_query_matches_standard_result(
            query="CountryCode = GB",
            filter_dict={"metadata__CountryCode__iexact": "GB"},
        )

        self.check_query_matches_standard_result(
            query='CountryCode = "GB"',
            filter_dict={"metadata__CountryCode__iexact": "GB"},
        )

        self.check_query_matches_standard_result(
            query='CountryCode = "GB"',
            filter_dict={"metadata__CountryCode__iexact": "GB"},
        )

        self.check_query_matches_standard_result_negated(
            query='CountryCode != "GB"',
            filter_dict={"metadata__CountryCode__iexact": "GB"},
        )

        self.check_query_matches_standard_result_negated(
            query='CountryCode != "G"',
            filter_dict={"metadata__CountryCode__iexact": "G"},
        )


if __name__ == "__main__":
    unittest.main()
