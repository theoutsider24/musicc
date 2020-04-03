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
from django.contrib.auth import get_user_model
import os
import shutil
from musicc.models.revisions.OpenDriveRevision import OpenDriveRevision
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from musicc.models.revisions.MusiccRevision import MusiccRevision
from django.conf import settings
from musicc.models.OpenDrive import OpenDrive
from musicc.models.Profile import Profile
from musicc.models.OpenScenario import OpenScenario
from musicc.models.MusiccScenario import MusiccScenario
from django.core.files.uploadedfile import UploadedFile
import zipfile
from musicc.utils.ZipSummary import ZipSummary
from musicc.utils.MusiccRecordBuilder import MusiccRecordBuilder

import logging

logger = logging.getLogger("musicc")

## Create the super user
def initialise_super_user():
    User = get_user_model()
    User.objects.create_superuser("admin", "admin@myproject.com", "password")
    current_user = User.objects.get(username='admin')
    Profile.create(user=current_user, has_agreed=True)

## Create user
def initialise_user(no_users, has_agreed=None):
    if has_agreed ==None:
        User = get_user_model()
        password='password'
        for i in range (0, no_users):
            username = 'user'+str(i)
            email = username+'@example.com'
            User.objects.create_user(username, email, password)
    else:
        User = get_user_model()
        password='password'
        for i in range (0, no_users):
            username = 'user'+str(i)
            email = username+'@example.com'
            user = User.objects.create_user(username, email, password)
            Profile.create(user=user, has_agreed=has_agreed)


revision_info_list = [
    {
        "musicc": {
            "path": os.path.join(
                settings.BASE_DIR,
                "..",
                "Sample Data",
                "MasterScenarios",
                "0.1.0",
                "xsd",
                "MUSICC_0.1.0.xsd",
            ),
            "revision": "0.1.0",
        },
        "openDrive": {
            "path": os.path.join(
                settings.BASE_DIR,
                "..",
                "Sample Data",
                "MasterScenarios",
                "0.1.0",
                "xsd",
                "OpenDRIVE_1.4H.xsd",
            ),
            "revision": "1.4H",
        },
        "openScenario": {
            "path": os.path.join(
                settings.BASE_DIR,
                "..",
                "Sample Data",
                "MasterScenarios",
                "0.1.0",
                "xsd",
                "OpenScenarioXSD.zip",
            ),
            "revision": "v0.9.1",
        },
    },
    {
        "musicc": {
            "path": os.path.join(
                settings.BASE_DIR,
                "..",
                "Sample Data",
                "MasterScenarios",
                "0.1.2",
                "xsd",
                "MUSICC_0.1.2.xsd",
            ),
            "revision": "0.1.2",
        },
        "openDrive": {
            "path": os.path.join(
                settings.BASE_DIR,
                "..",
                "Sample Data",
                "MasterScenarios",
                "0.1.2",
                "xsd",
                "OpenDRIVE_1.4H.xsd",
            ),
            "revision": "1.4H",
        },
        "openScenario": {
            "path": os.path.join(
                settings.BASE_DIR,
                "..",
                "Sample Data",
                "MasterScenarios",
                "0.1.2",
                "xsd",
                "OpenScenarioXSD.zip",
            ),
            "revision": "v0.9.1",
        },
    },
]


latest_revision_info = revision_info_list[-1]

outdated_revision_info = {
    "musicc": {
        "path": os.path.join(
            settings.BASE_DIR,
            "..",
            "Sample Data",
            "MasterScenarios",
            "0.0.9",
            "xsd",
            "MUSICC_0.0.9.xsd",
        ),
        "revision": "0.0.9",
    },
    "openDrive": {
        "path": os.path.join(
            settings.BASE_DIR,
            "..",
            "Sample Data",
            "MasterScenarios",
            "0.0.9",
            "xsd",
            "OpenDRIVE_1.4H.xsd",
        ),
        "revision": "1.4H",
    },
    "openScenario": {
        "path": os.path.join(
            settings.BASE_DIR,
            "..",
            "Sample Data",
            "MasterScenarios",
            "0.0.9",
            "xsd",
            "OpenScenarioXSD.zip",
        ),
        "revision": "v0.9.1",
    },
}

## Generate test data for an old revision of MUSICC
def create_outdated_scenarios(current_user, outdated_revision_info=outdated_revision_info):
    initialise_revision_tables(current_user, outdated_revision_info)
    initialise_scenario_tables(
        current_user,
        outdated_revision_info["musicc"]["revision"],
        "tests/test_files/Test Data/0.0.9/master_scenarios.zip",
    )

## Generate test data for an old revision of MUSICC, using the URL for revision creation
def create_outdated_scenarios_via_url(client, current_user):
    initialise_revision_tables_via_url(client, current_user, outdated_revision_info)
    initialise_scenario_tables(
        current_user,
        outdated_revision_info["musicc"]["revision"],
        "tests/test_files/Test Data/0.0.9/master_scenarios.zip",
    )

## Upload XSDs for a revision
def initialise_revision_tables(current_user, revision_info=latest_revision_info):
    with open(revision_info["openDrive"]["path"], "rb") as odrRevFile:
        OpenDriveRevision.create(
            UploadedFile(file=odrRevFile, name=""),
            revision_info["openDrive"]["revision"],
            current_user,
            True,
        )
    with open(revision_info["openScenario"]["path"], "rb") as oscRevFile:
        OpenScenarioRevision.create(
            UploadedFile(file=oscRevFile, name=""),
            revision_info["openScenario"]["revision"],
            current_user,
            True,
        )
    with open(revision_info["musicc"]["path"], "rb") as musRevFile:
        MusiccRevision.create(
            UploadedFile(file=musRevFile, name=""),
            revision_info["musicc"]["revision"],
            current_user,
            True,
        )

## Upload XSDs for a revision using the url
def initialise_revision_tables_via_url(
    client, current_user, revision_info=latest_revision_info
):
    with open(revision_info["openDrive"]["path"], "rb") as odrRevFile:
        client.post(
            "http://localhost:8000/upload_revisions",
            {
                "open_drive_xsd": odrRevFile,
                "open_drive_rev_id": revision_info["openDrive"]["revision"],
            },
        )

    with open(revision_info["openScenario"]["path"], "rb") as oscRevFile:
        client.post(
            "http://localhost:8000/upload_revisions",
            {
                "open_scenario_xsd": oscRevFile,
                "open_scenario_rev_id": revision_info["openScenario"]["revision"],
            },
        )

    with open(revision_info["musicc"]["path"], "rb") as musRevFile:
        client.post(
            "http://localhost:8000/upload_revisions",
            {
                "musicc_xsd": musRevFile,
                "musicc_rev_id": revision_info["musicc"]["revision"],
            },
        )

    musicc_revision = MusiccRevision.active_objects.get(
        revision=revision_info["musicc"]["revision"]
    )
    musicc_revision.activate()

## Upload scenarios for a specific revision
def initialise_scenario_tables(
    current_user,
    revision="0.1.2",
    filename="tests/test_files/Test Data/0.1.2/master_scenarios.zip",
):
    if zipfile.is_zipfile(os.path.join(settings.BASE_DIR, filename)):
        zip_summary = ZipSummary(
            UploadedFile(
                file=os.path.join(settings.BASE_DIR, filename),
                name="master_scenarios.zip",
            )
        )
        musicc_builder = MusiccRecordBuilder(zip_summary, current_user, revision)
        musicc_builder.process_musicc_files()
        if len(musicc_builder.musicc_context.error_list) == 0:
            logger.info("Successfully ingested file")
        else:
            logger.error(musicc_builder.musicc_context.error_list)
    else:
        logger.error("File provided is not a valid zip file")

## Modify the media root to be within test_artefacts
def set_media_root():
    settings.MEDIA_ROOT = os.path.join(
        settings.BASE_DIR, "..", "test_artefacts", "media", "img"
    )

## Clean up the temporary media folder used in test configurations and reset the media root to the actual configuration
def clear_media_root():
    if os.path.exists(settings.MEDIA_ROOT) and os.path.isdir(settings.MEDIA_ROOT):
        shutil.rmtree(os.path.join(settings.BASE_DIR, "..", "test_artefacts", "media"), True)

    settings.MEDIA_ROOT = os.path.join(settings.STATIC_ROOT, "media", "img")
