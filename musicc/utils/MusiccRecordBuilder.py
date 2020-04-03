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
from musicc.utils.ZipSummary import ZipSummary
from lxml import etree
import zipfile
from musicc.models.OpenScenario import OpenScenario
from musicc.models.OpenDrive import OpenDrive
from musicc.models.MusiccScenario import MusiccScenario
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.Catalog import Catalog, CatalogMapping
from musicc.models.ScenarioImage import ScenarioImage
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth import get_user_model
from musicc.models.logs.ChangeLog import (
    ChangeLog,
    ChangeMusiccMapping,
    ChangeOpenDriveMapping,
    ChangeOpenScenarioMapping,
    ChangeCatalogMapping,
)
from musicc.utils.xml_functions import convert_xml_to_json

User = get_user_model()

import logging
import os
import tempfile
from io import BytesIO
from musicc.utils.xml_functions import replace_value_in_xml
from musicc.utils.openScenario_version_map import openScenario_version_map
import re
from musicc.utils.MusiccRecordContext import MusiccRecordContext


logger = logging.getLogger("musicc")


class MusiccRecordBuilder:
    def __init__(
        self, zip_summary: ZipSummary, current_user: User, revision_number=None
    ):
        self.musicc_context = MusiccRecordContext(
            zip_summary, current_user, revision_number
        )

    def validate(self):
        for musicc_filename in self.musicc_context.zip_summary.musicc_list:
            self.base_directory = "/".join(musicc_filename.split("/")[:-1])
            self.base_directory = (
                self.base_directory + "/"
                if self.base_directory
                else self.base_directory
            )

            try:
                (
                    found_open_scenario_file,
                    found_open_drive_file,
                ) = self.musicc_context.validate_referenced_files(musicc_filename)
                self.verify_referenced_catalogs_are_defined(found_open_scenario_file)
                self.validate_musicc_type(
                    self.musicc_context.zip_summary.zip_file.open(
                        musicc_filename
                    ).read()
                )

            except etree.DocumentInvalid as err:
                self.musicc_context.error_list[musicc_filename] = []
                for e in err.error_log:
                    logger.error(e.message)
                    self.musicc_context.error_list[musicc_filename].append(e.message)

            except Exception as e:
                self.musicc_context.error_list[musicc_filename] = []
                logger.exception(e)
                self.musicc_context.error_list[musicc_filename].append(str(e))

    def create_musicc_record(self, musicc_filename):

        self.musicc_context.uploaded_log_list = []
        self.catalog_tuple_list = []

        (
            found_open_scenario_file,
            found_open_drive_file,
        ) = self.musicc_context.validate_referenced_files(musicc_filename)

        referenced_catalog_list = self.verify_referenced_catalogs_are_defined(
            found_open_scenario_file
        )

        self.validate_musicc_type(
            self.musicc_context.zip_summary.zip_file.open(musicc_filename).read()
        )
        
        open_scenario_revision = self.musicc_context.revision.open_scenario_revision.revision
        try:
            logic_element = openScenario_version_map['maps'][open_scenario_revision]['logic']
        except:
            logic_element = openScenario_version_map['maps']['default']['logic']
        open_scenario_post_processing = [(logic_element, "filepath", "")]
        modified_open_scenario_etree = self.xml_post_processor(
            found_open_scenario_file, open_scenario_post_processing
        )

        self.create_catalogs(referenced_catalog_list)
        catalog_id_string_list = self.get_ascending_catalog_id_list(
            self.catalog_tuple_list
        )

        open_scenario_record = self.musicc_context.create_logged_open_scenario_record(
            catalog_id_string_list,
            modified_open_scenario_etree,
            found_open_scenario_file,
        )

        for catalog_tuple in self.catalog_tuple_list:
            CatalogMapping.create(
                open_scenario_record, catalog_tuple, self.base_directory
            )

        open_drive_record = self.musicc_context.create_logged_record_from_file_path(
            ChangeOpenDriveMapping, found_open_drive_file, OpenDrive
        )

        new_open_scenario_filename = (
            str(open_scenario_record.get_human_readable_id()) + ".xosc"
        )
        new_open_drive_filename = (
            str(open_drive_record.get_human_readable_id()) + ".xodr"
        )

        musicc_post_processing = [
            ("OpenSCENARIO", "filepath", new_open_scenario_filename),
            ("OpenDRIVE", "filepath", new_open_drive_filename),
        ]

        modified_musicc_etree = self.xml_post_processor(
            musicc_filename, musicc_post_processing
        )

        musicc_record = self.musicc_context.create_logged_record_from_etree(
            ChangeMusiccMapping, modified_musicc_etree, musicc_filename, MusiccScenario
        )

        for uploaded_log_map in self.musicc_context.uploaded_log_list:
            uploaded_log_map.musicc = musicc_record
            uploaded_log_map.save()

        self.musicc_context.upload_images(musicc_filename, musicc_record)
        self.musicc_context.upload_resources(musicc_filename, musicc_record)

    def get_ascending_catalog_id_list(self, catalog_tuple_list):
        catalog_id_list = [catalog_tuple[0].id for catalog_tuple in catalog_tuple_list]

        catalog_id_list.sort()
        catalog_id_string_list = ",".join(map(str, catalog_id_list))

        return catalog_id_string_list

    def create_catalogs(self, referenced_catalog_list):

        for referenced_catalog in referenced_catalog_list:
            directory = referenced_catalog[1]
            file_name = referenced_catalog[0]
            with self.musicc_context.zip_summary.zip_file.open(
                "{0}/{1}".format(directory, file_name)
            ) as f:

                uploaded_catalog_mapping = self.musicc_context.create_change_log_mapping(
                    ChangeCatalogMapping, file_name
                )

                catalog = Catalog.create(
                    UploadedFile(file=f, name=f.name), self.musicc_context.current_user
                )

                self.musicc_context.update_change_log_mapping(
                    uploaded_catalog_mapping, catalog
                )

                self.musicc_context.uploaded_log_list.append(uploaded_catalog_mapping)

                self.catalog_tuple_list.append((catalog, referenced_catalog))

    def process_musicc_files(self):

        self.musicc_context.create_change_log()

        for musicc_filename in self.musicc_context.zip_summary.musicc_list:
            self.base_directory = "/".join(musicc_filename.split("/")[:-1])
            self.base_directory = (
                self.base_directory + "/"
                if self.base_directory
                else self.base_directory
            )

            try:

                self.create_musicc_record(musicc_filename)

            except etree.DocumentInvalid as err:
                self.musicc_context.error_list[musicc_filename] = []
                for e in err.error_log:
                    logger.error(e.message)
                    self.musicc_context.error_list[musicc_filename].append(e.message)

            except Exception as e:
                self.musicc_context.error_list[musicc_filename] = []
                logger.exception(e)
                self.musicc_context.error_list[musicc_filename].append(str(e))

    def xml_post_processor(self, filename, find_array):
        with self.musicc_context.zip_summary.zip_file.open(filename) as file:
            xml_etree = etree.parse(file)
            xml_etree_root = xml_etree.getroot()
            for find_field in find_array:
                replace_value_in_xml(
                    xml_root=xml_etree_root,
                    tag_name=find_field[0],
                    attribute_name=find_field[1],
                    value=find_field[2],
                )
        return xml_etree

    def find_all_catalog_references(self, filename):
        with self.musicc_context.zip_summary.zip_file.open(
            filename
        ) as open_scenario_file:
            root_node = etree.parse(open_scenario_file).getroot()
            references = [
                (
                    catalog_reference.get("catalogName"),
                    catalog_reference.get("entryName"),
                )
                for catalog_reference in root_node.xpath("//CatalogReference")
            ]
        return references

    def find_all_referenced_catalog_directories(self, filename):
        with self.musicc_context.zip_summary.zip_file.open(
            filename
        ) as open_scenario_file:
            root_node = etree.parse(open_scenario_file).getroot()
            open_scenario_revision = self.musicc_context.revision.open_scenario_revision.revision
            try:
                catalog_location = openScenario_version_map['maps'][open_scenario_revision]['catalog']
            except:
                catalog_location = openScenario_version_map['maps']['default']['catalog']
            definitions = [
                catalog_definition.find("Directory").get("path").strip("/")
                for catalog_definition in root_node.find(catalog_location).getchildren()
                if catalog_definition.find("Directory").get("path") != ""
            ]

        return definitions

    def verify_referenced_catalogs_are_defined(self, filename):
        catalog_references = self.find_all_catalog_references(filename)
        referenced_catalog_directories = self.find_all_referenced_catalog_directories(
            filename
        )

        catalog_errors = []

        # Filter out discovered catalogs in directories which are not referenced
        catalog_tuple_list = list(
            filter(
                lambda tuple: tuple[1].replace(self.base_directory, "")
                in referenced_catalog_directories,
                self.musicc_context.zip_summary.catalog_tuple_list,
            )
        )

        referenced_set = set()

        for catalog in catalog_references:
            definition_subset = [
                definition
                for definition in catalog_tuple_list
                if set(catalog).issubset(definition)
            ]
            if not any(definition_subset):
                catalog_errors.append("Catalog {0} is not defined".format(catalog))
            else:
                for definition in definition_subset:
                    referenced_set.add((definition[0], definition[1], definition[2]))
        if catalog_errors:
            raise Exception(catalog_errors)
        else:
            return referenced_set

    def has_parameter_stochastics(self, musicc_json):
        has_parameter_stochastics = False
        try:
            open_scenario_parameters = musicc_json["MUSICCScenario"][
                "ParameterStochastics"
            ]["OpenScenario"]["ParameterGroup"].get("Parameter")
            if open_scenario_parameters:
                has_parameter_stochastics = True
        except KeyError:
            pass
        return has_parameter_stochastics

    def validate_musicc_type(self, musicc_blob):
        musicc_blob = bytes(musicc_blob)
        musicc_json = convert_xml_to_json(musicc_blob)
        try:
            musicc_type = musicc_json["MUSICCScenario"]["Metadata"]["ScenarioType"].get(
                "@value"
            )
            parameter_stochastics_present = self.has_parameter_stochastics(musicc_json)

            if musicc_type == "Logical" and not parameter_stochastics_present:
                raise Exception(
                    "ScenarioType is {0} but scenario has no parameter stochastics".format(
                        musicc_type
                    )
                )
            elif musicc_type == "Concrete" and parameter_stochastics_present:
                raise Exception(
                    "ScenarioType is {0} but scenario has parameter stochastics".format(
                        musicc_type
                    )
                )
        except KeyError:
            pass

