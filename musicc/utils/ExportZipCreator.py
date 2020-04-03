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
from musicc.models.QueryCache import QueryCache
from musicc.utils import tools
import os, sys
import shutil
from musicc.models.Catalog import CatalogMapping
from lxml.etree import fromstring, Comment, tostring
from musicc.utils.openScenario_version_map import openScenario_version_map
from musicc.utils.xml_functions import replace_value_in_xml, convert_xml_to_json
from numpy.random import normal, uniform
import math
import numpy
from datetime import datetime
from zipfile import ZipFile, ZIP_STORED
import copy


class ExportZipCreator(ZipFile):
    numpy_state = None

    def select_value(dict):
        option_list = dict.get("List").get("ListElement")
        options = []
        equally_distributed_options = []

        for element in option_list:
            option = {}
            try:
                option["probability"] = float(element.get("@probabilityOfOccurence"))
            except:
                equally_distributed_options.append(element)
                continue
            option["value"] = element.get("@value")
            if options:
                option["probability"] += options[-1]["probability"]
            options.append(option)

        remaining_space = 1
        if options:
            remaining_space = remaining_space - options[-1]["probability"]
        if equally_distributed_options and (
            not options or options[-1]["probability"] < 1
        ):
            for element in equally_distributed_options:
                option = {}
                option["value"] = element.get("@value")
                option["probability"] = remaining_space / len(
                    equally_distributed_options
                )
                if options:
                    option["probability"] += options[-1]["probability"]
                options.append(option)
            # Set last option to 1 in case it's 0.999... recurring
            options[-1]["probability"] = 1

        random_number = uniform(0, 1)
        for option in options:
            if random_number < option["probability"]:
                return option["value"]

    def apply_random_parameters(self, parameter_list, target_file_blob, musicc_scenario):
        etree = fromstring(target_file_blob)
        open_scenario_revision = musicc_scenario.revision.open_scenario_revision.revision
        try:
            parameter_element = openScenario_version_map['maps'][open_scenario_revision]['parameterDeclaration']
        except:
            parameter_element = openScenario_version_map['maps']['default']['parameterDeclaration']
        parameters = etree.find(parameter_element)

        if not isinstance(parameter_list, list):
            parameter_list = [parameter_list]

        for parameter in parameter_list:
            param_type = parameter["@type"]
            name = parameter["@name"]
            distribution_type = list(parameter["Distribution"])[0]
            random_value = self.distributions[distribution_type](
                parameter["Distribution"].get(distribution_type)
            )

            if param_type == "int":
                random_value = int(random_value)

            if not random_value is None:
                for parameter in parameters:
                    if parameter.get("name") == name:
                        parameter.set("value", str(random_value))

        return tostring(etree, encoding="utf-8", xml_declaration=True)

    def add_musicc_metadata_to_osc(self, musicc_blob, osc_blob):
        musicc_etree = fromstring(musicc_blob)
        osc_etree = fromstring(osc_blob)

        musicc_file_header = (
            tostring(musicc_etree.find("FileHeader"))
            .decode("utf-8")
            .replace("--", "##")
            .encode("utf-8")
        )
        musicc_file_header_comment = Comment(musicc_file_header)
        musicc_file_header_comment.tail = "\n"

        musicc_metadata = (
            tostring(musicc_etree.find("Metadata"))
            .decode("utf-8")
            .replace("--", "##")
            .encode("utf-8")
        )
        musicc_metadata_comment = Comment(musicc_metadata)
        musicc_metadata_comment.tail = "\n"

        osc_etree.insert(0, musicc_metadata_comment)
        osc_etree.insert(0, musicc_file_header_comment)
        return tostring(osc_etree, encoding="utf-8", xml_declaration=True)

    def add_musicc_id_to_osc(self, musicc_id, osc_blob):
        osc_etree = fromstring(osc_blob)
        comment = Comment("MUSICC id: " + musicc_id)
        comment.tail = "\n"
        osc_etree.insert(0, comment)
        return tostring(osc_etree, encoding="utf-8", xml_declaration=True)

    def add_odr_reference_to_osc(self, odr_id, osc_blob, musicc_scenario):
        osc_etree = fromstring(osc_blob)
        open_scenario_revision = musicc_scenario.revision.open_scenario_revision.revision
        try:
            logic_element = openScenario_version_map['maps'][open_scenario_revision]['logic']
        except:
            logic_element = openScenario_version_map['maps']['default']['logic']
        replace_value_in_xml(
            xml_root=osc_etree,
            tag_name=logic_element,
            attribute_name="filepath",
            value="{0}.xodr".format(odr_id),
        )
        return tostring(osc_etree, encoding="utf-8", xml_declaration=True)

    distributions = {
        "NormalDistribution": lambda dict: normal(
            dict.get("@expectedValue"), math.sqrt((dict.get("@variance")))
        ),
        "UniformDistribution": lambda dict: uniform(
            dict.get("@lowerLimit"), dict.get("@upperLimit")
        ),
        "SingleValues": select_value,
    }

    def __init__(
        self,
        file_path,
        results,
        numpy_state=None,
        native=True,
        concrete_per_logical=1,
        exclude_resources=False,
        exclude_images=False,
    ):
        super(ExportZipCreator, self).__init__(
            file_path, mode="w", compression=ZIP_STORED
        )
        self.file_path = file_path
        if numpy_state is not None:
            numpy.random.set_state(numpy_state)
        else:
            numpy.random.seed(None)
        self.numpy_state = numpy.random.get_state()

        for musicc_scenario in results.all():

            scenario_dir_id = str(musicc_scenario.get_human_readable_id())

            musicc_blob = bytes(musicc_scenario.musicc_blob)
            musicc_json = convert_xml_to_json(musicc_blob)

            try:
                open_scenario_parameters = musicc_json["MUSICCScenario"][
                    "ParameterStochastics"
                ]["OpenScenario"]["ParameterGroup"].get("Parameter")
            except KeyError:
                open_scenario_parameters = None

            open_scenario_blob = bytes(musicc_scenario.scenario.open_scenario_blob)

            open_scenario_blob_list = []

            for _ in range(
                concrete_per_logical
                if musicc_scenario.metadata["ScenarioType"] == "Logical"
                else 1
            ):
                temp_open_scenario_blob = copy.copy(open_scenario_blob)
                if not native:
                    if open_scenario_parameters:
                        temp_open_scenario_blob = self.apply_random_parameters(
                            open_scenario_parameters, temp_open_scenario_blob, musicc_scenario
                        )
                    temp_open_scenario_blob = self.add_musicc_metadata_to_osc(
                        musicc_blob, temp_open_scenario_blob
                    )
                    temp_open_scenario_blob = self.add_musicc_id_to_osc(
                        str(musicc_scenario.get_human_readable_id()),
                        temp_open_scenario_blob,
                    )

                temp_open_scenario_blob = self.add_odr_reference_to_osc(
                    str(musicc_scenario.open_drive.get_human_readable_id()),
                    temp_open_scenario_blob,
                    musicc_scenario
                )
                open_scenario_blob_list.append(temp_open_scenario_blob)

            if native:
                self.create_file_from_database_blob(
                    os.path.join(
                        scenario_dir_id,
                        "{0}.xmus".format(musicc_scenario.get_human_readable_id()),
                    ),
                    musicc_blob,
                )

            self.create_file_from_database_blob(
                os.path.join(
                    scenario_dir_id,
                    "{0}.xodr".format(
                        musicc_scenario.open_drive.get_human_readable_id()
                    ),
                ),
                bytes(musicc_scenario.open_drive.open_drive_blob),
            )

            for i, blob in enumerate(open_scenario_blob_list):
                self.create_file_from_database_blob(
                    os.path.join(
                        scenario_dir_id,
                        "{0}{1}.xosc".format(
                            musicc_scenario.scenario.get_human_readable_id(),
                            "_" + str(i) if len(open_scenario_blob_list) > 1 else "",
                        ),
                    ),
                    blob,
                )

            self.create_catalog_files_from_database_blob(
                musicc_scenario, scenario_dir_id
            )

            if not exclude_images:
                for i, image in enumerate(musicc_scenario.images.all()):
                    self.writestr(
                        os.path.join(
                            scenario_dir_id,
                            "images/{0}_{1}.{2}".format(
                                musicc_scenario.get_human_readable_id(),
                                i + 1,
                                image.file_type,
                            ),
                        ),
                        image.image.read(),
                    )

            if not exclude_resources:
                for resource_mapping in musicc_scenario.resourcemapping_set.filter(
                    active=True
                ):
                    file_contents = resource_mapping.resource.file.read()
                    self.writestr(
                        os.path.join(
                            scenario_dir_id,
                            "resources/{0}".format(resource_mapping.filename),
                        ),
                        file_contents,
                    )

        self.close()

    def create_catalog_files_from_database_blob(self, musicc_scenario, scenario_dir_id):
        catalogs = musicc_scenario.scenario.catalog.all()

        for catalog in catalogs:
            catalog_map = CatalogMapping.active_objects.get(
                catalog=catalog, open_scenario=musicc_scenario.scenario
            )
            self.create_file_from_database_blob(
                os.path.join(
                    scenario_dir_id, catalog_map.directory, catalog_map.filename
                ),
                bytes(catalog.catalog_blob),
            )

    def create_file_from_database_blob(self, file_path, blob):
        self.writestr(file_path, blob.decode("utf-8"))

    def create_catalog_dirs(self, catalog_list, base_dir):
        for catalog_dir in catalog_list:
            if catalog_list[catalog_dir]:
                os.makedirs(os.path.join(base_dir, catalog_list[catalog_dir]))

    def create_catalog_type_dict(self, open_scenario_json):
        catalogs_list = list(
            tools.find_keys_in_dictionary("Catalogs", open_scenario_json)
        )

        catalog_directory_paths = list(
            tools.find_keys_in_dictionary("@path", catalogs_list[0])
        )

        catalog_type_list = []
        for catalog_type in catalogs_list[0]:
            catalog_type_list.append(catalog_type)

        catalog_directories_to_create = dict(
            zip(catalog_type_list, catalog_directory_paths)
        )

        return catalog_directories_to_create
