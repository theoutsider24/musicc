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
from musicc.models.OpenScenario import OpenScenario
from musicc.models.OpenDrive import OpenDrive
from musicc.models.MusiccScenario import MusiccScenario
from lxml import etree
from musicc.utils.ZipSummary import ZipSummary
from musicc.models.logs.ChangeLog import ChangeOpenScenarioMapping
from musicc.models.logs.ChangeLog import ChangeLog
from io import BytesIO
from django.core.files import File
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.ScenarioImage import ScenarioImage
from musicc.models.Resource import ResourceMapping
import re
import logging
import os

logger = logging.getLogger("musicc")


class MusiccRecordContext:
    def __init__(self, zip_summary, current_user, revision_number=None):
        self.zip_summary = zip_summary
        self.current_user = current_user
        self.error_list = {}
        self.uploaded_log_list = []

        if revision_number:
            try:
                self.revision = MusiccRevision.active_objects.get(
                    revision=revision_number
                )
            except MusiccRevision.DoesNotExist:
                raise Exception("{0} is not a valid revision".format(revision_number))
        else:
            self.revision = MusiccRevision.latest_revision()

    def create_change_log(self):
        self.change_log = ChangeLog.create(
            "CREATE",
            self.current_user,
            self.revision,
            self.zip_summary.uploaded_file_name,
            self.zip_summary.zip_hash,
        )

    def upload_images(self, musicc_filename, musicc_record):
        for image in self.zip_summary.image_list:
            musicc_file_to_match = os.path.splitext(os.path.basename(musicc_filename))[
                0
            ]
            image_file_to_match = re.sub(r"_\d+(\..*)", "", image.split("/")[-1])

            if musicc_file_to_match == image_file_to_match:
                with self.zip_summary.zip_file.open(image) as image_file:
                    scen_img = ScenarioImage.create(
                        File(file=image_file, name=image), self.current_user
                    )
                    musicc_record.images.add(scen_img)

    def upload_resources(self, musicc_filename, musicc_record):
        for resource in self.zip_summary.resource_list:
            resource_file_name = os.path.split(resource)[-1]
            resource_file_directory = os.path.split(os.path.dirname(resource))[-1]
            musicc_file_to_match = os.path.splitext(os.path.basename(musicc_filename))[
                0
            ]
            if resource_file_directory == "resources_" + musicc_file_to_match or (
                resource_file_directory == "resources"
                and os.path.dirname(musicc_filename)
                == os.path.split(os.path.dirname(resource))[0]
            ):

                with self.zip_summary.zip_file.open(resource, 'r') as resource_file:
                    ResourceMapping.create(
                        File(file=BytesIO(resource_file.read()), name=resource_file_name), musicc_record, self.current_user
                    )

    def validate_referenced_files(self, musicc_filename):
        with self.zip_summary.zip_file.open(musicc_filename) as musicc_file:
            file_content = musicc_file.read()
            MusiccScenario.validate(
                self.revision,
                file_content,
                "MUSICCScenario",
            )
            root_node = etree.fromstring(file_content)
            open_scenario_element = root_node.find("OpenSCENARIO")
            open_drive_element = root_node.find("OpenDRIVE")

        found_open_scenario_file = self.find_file_from_element(
            open_scenario_element, self.zip_summary.open_scenario_list
        )

        found_open_drive_file = self.find_file_from_element(
            open_drive_element, self.zip_summary.open_drive_list
        )

        OpenDrive.validate(
            self.revision.open_drive_revision,
            self.zip_summary.zip_file.open(found_open_drive_file).read(),
            "OpenDRIVE",
        )
        OpenScenario.validate(
            self.revision.open_scenario_revision,
            self.zip_summary.zip_file.open(found_open_scenario_file).read(),
            "OpenSCENARIO",
        )
        return (found_open_scenario_file, found_open_drive_file)

    def find_file_in_filename_list(self, filename, filename_list):
        for file in filename_list:
            if filename == file.split("/")[-1]:
                return file

    def find_file_from_element(self, element: etree.Element, filename_list):
        filename = element.get("filepath")
        found_file = self.find_file_in_filename_list(filename, filename_list)
        if found_file:
            return found_file
        else:
            raise Exception("Cannot find file {0}".format(filename))

    def create_logged_record_from_etree(
        self, change_log_model, etree_object, filename, model
    ):
        change_log_mapping = self.create_change_log_mapping(change_log_model, filename)

        record = self.create_record_from_etree(
            model, etree_object, filename, self.revision
        )

        logger.info(
            "Uploaded {0} filename: {1} ID: {2}".format(
                model.__name__, filename, record.get_human_readable_id()
            )
        )

        self.update_change_log_mapping(change_log_mapping, record)

        self.uploaded_log_list.append(change_log_mapping)

        return record

    def create_logged_open_scenario_record(
        self, catalog_id_string_list, etree_object, filename
    ):
        change_log_mapping = self.create_change_log_mapping(
            ChangeOpenScenarioMapping, filename
        )

        record = self.create_open_scenario_record_from_etree(
            etree_object=etree_object,
            filename=filename,
            catalog_id_list=catalog_id_string_list,
        )

        logger.info(
            "Uploaded OpenScenario filename: {0} ID: {1}".format(
                filename, record.get_human_readable_id()
            )
        )

        self.update_change_log_mapping(change_log_mapping, record)

        self.uploaded_log_list.append(change_log_mapping)

        return record

    def create_logged_record_from_file_path(self, change_log_model, filename, model):
        change_log_mapping = self.create_change_log_mapping(change_log_model, filename)

        record = self.create_record_from_file_path(model, filename)

        logger.info(
            "Uploaded {0} filename: {1} ID: {2}".format(
                model.__name__, filename, record.get_human_readable_id()
            )
        )

        self.update_change_log_mapping(change_log_mapping, record)

        self.uploaded_log_list.append(change_log_mapping)

        return record

    def create_change_log_mapping(self, change_log_model, filename):
        change_log_mapping = change_log_model.create(
            filename=filename, change_log=self.change_log
        )

        return change_log_mapping

    def update_change_log_mapping(self, change_log_mapping, record):
        change_log_mapping.record = record
        change_log_mapping.save()

    def create_record_from_file_path(self, model, file_path):
        if isinstance(file_path, str):
            with self.zip_summary.zip_file.open(file_path) as opened_file:
                record = model.create(
                    File(file=opened_file, name=file_path), self.current_user
                )
                return record
        else:
            raise Exception("File path parameter should be a string")

    def create_record_from_etree(self, model, etree_object, filename, revision=None):
        if isinstance(etree_object, etree._ElementTree):
            if filename:
                file_like_etree = BytesIO(
                    etree.tostring(etree_object, encoding="utf-8", xml_declaration=True)
                )

                record = model.create(
                    file=File(file=file_like_etree, name=filename),
                    user=self.current_user,
                    revision=revision,
                )

                return record
            else:
                raise Exception("Filename parameter expected")

        else:
            raise Exception("Etree parameter should be of type etree._ElementTree")

    def create_open_scenario_record_from_etree(
        self, etree_object, filename, catalog_id_list
    ):
        if isinstance(etree_object, etree._ElementTree):
            if filename:
                file_like_etree = BytesIO(
                    etree.tostring(etree_object, encoding="utf-8", xml_declaration=True)
                )
                record = OpenScenario.create(
                    file=File(file=file_like_etree, name=filename),
                    user=self.current_user,
                    catalog_id_list=catalog_id_list,
                )
                return record
            else:
                raise Exception("Filename parameter expected")

        else:
            raise Exception("Etree parameter should be of type etree._ElementTree")
