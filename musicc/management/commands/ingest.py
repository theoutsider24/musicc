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
from musicc.views import curation
from django.core.management.base import BaseCommand
import os
from django.conf import settings
from musicc.tests.utilities import (
    initialise_revision_tables,
    initialise_super_user,
    create_outdated_scenarios,
    outdated_revision_info,
    revision_info_list
)
from django.contrib.auth import get_user_model

User = get_user_model()


from musicc.models.OpenDrive import OpenDrive
from musicc.models.OpenScenario import OpenScenario
from musicc.models.MusiccScenario import MusiccScenario
from django.core.files.uploadedfile import UploadedFile
from lxml import etree
import logging
import zipfile
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.ZipSummary import ZipSummary
from musicc.utils.MusiccRecordBuilder import MusiccRecordBuilder


logger = logging.getLogger("musicc")


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("-z", "--zip", type=str, help="Zip file to ingest")
        parser.add_argument("-r", "--revision", type=str, help="MUSICC Revision")
        parser.add_argument("-dds", "--dummy_data_suffix", type=str, help="Add suffix to revision if dummy data")

    def handle(self, *args, **options):

        zip = options["zip"]
        zip_name = zip.split("/")[-1]
        try:
            initialise_super_user()
        except:
            pass
        current_user = User.objects.get(username="admin")
        dummy_data_suffix = options["dummy_data_suffix"]
        if dummy_data_suffix:
            os_revision = outdated_revision_info["openScenario"]['revision']
            outdated_revision_info["openScenario"]['revision']=os_revision+dummy_data_suffix
            outdated_revision_info["openScenario"]["path"] = os.path.join(settings.BASE_DIR,"..","Sample Data","DummyScenarios",'0.0.9',"xsd","OpenScenarioXSD.zip")
            od_revision = outdated_revision_info["openDrive"]['revision']
            outdated_revision_info["openDrive"]['revision']=od_revision+dummy_data_suffix
            outdated_revision_info["openDrive"]["path"] = os.path.join(settings.BASE_DIR,"..","Sample Data","DummyScenarios",'0.1.2',"xsd","OpenDRIVE_1.4H.xsd")
            musicc_revision = outdated_revision_info["musicc"]['revision']
            outdated_revision_info["musicc"]['revision']=musicc_revision+dummy_data_suffix
            outdated_revision_info["musicc"]["path"] = os.path.join(settings.BASE_DIR,"..","Sample Data","DummyScenarios",'0.0.9',"xsd","MUSICC_0.0.9.xsd")
        create_outdated_scenarios(current_user, outdated_revision_info=outdated_revision_info)
        for revision in revision_info_list:
            if dummy_data_suffix:
                os_revision = revision["openScenario"]['revision']
                musicc_revision = revision["musicc"]['revision']
                od_revision = revision["openDrive"]['revision']
                revision["openScenario"]['revision']=os_revision+dummy_data_suffix
                revision["openScenario"]["path"] = os.path.join(settings.BASE_DIR,"..","Sample Data","DummyScenarios",musicc_revision,"xsd","OpenScenarioXSD.zip")
                revision["openDrive"]['revision']=od_revision+dummy_data_suffix
                revision["openDrive"]["path"] = os.path.join(settings.BASE_DIR,"..","Sample Data","DummyScenarios",musicc_revision,"xsd","OpenDRIVE_1.4H.xsd")
                revision["musicc"]['revision']=musicc_revision+dummy_data_suffix
                revision["musicc"]["path"] = os.path.join(settings.BASE_DIR,"..","Sample Data","DummyScenarios",musicc_revision,"xsd","MUSICC_"+musicc_revision+".xsd")
            initialise_revision_tables(current_user, revision)
        if zipfile.is_zipfile(zip):
            zip_summary = ZipSummary(UploadedFile(file=zip, name=zip_name))
            musicc_builder = MusiccRecordBuilder(zip_summary, current_user, options["revision"])
            musicc_builder.process_musicc_files()
            if  len(musicc_builder.musicc_context.error_list) == 0:
                logger.info("Successfully ingested file")
            else:
                logger.error(musicc_builder.musicc_context.error_list)
        else:
            logger.error("File provided is not a valid zip file")

