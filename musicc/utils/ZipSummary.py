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
import zipfile
from django.core.files.uploadedfile import UploadedFile
import os
from lxml import etree
from io import BytesIO
import imghdr

import logging
from musicc.utils.tools import get_uploaded_zip_file_hash


logger = logging.getLogger("musicc")


class ZipSummary:
    def __init__(self, uploaded_zip_file: UploadedFile):
        self.musicc_list = []
        self.open_scenario_list = []
        self.open_drive_list = []
        self.catalog_tuple_list = []
        self.image_list = []
        self.resource_list = []
        self.uploaded_file_name = uploaded_zip_file.name
    
        if zipfile.is_zipfile(uploaded_zip_file.file):
            self.zip_file = zipfile.ZipFile(uploaded_zip_file.file)
            for file in self.zip_file.infolist():
                file_extension = os.path.splitext(file.filename)[1]
                if file_extension == ".xmus":
                    self.musicc_list.append(file.filename)
                elif file_extension == ".xosc":
                    self.determine_catalog(file.filename)
                elif file_extension == ".xodr":
                    self.open_drive_list.append(file.filename)
                elif file_extension:
                    with self.zip_file.open(file.filename) as potential_image_file:
                        if imghdr.what("", h=potential_image_file.read()):
                            self.image_list.append(file.filename)
                    self.resource_list.append(file.filename)

            self.zip_hash = get_uploaded_zip_file_hash(uploaded_zip_file)

        else:
            raise Exception("Uploaded file not a zip-file")

    def determine_catalog(self, xosc_filename: str):
        with self.zip_file.open(xosc_filename) as open_scenario_file:
            root_node = etree.parse(open_scenario_file).getroot()
            if root_node.find("Catalog") is None:
                self.open_scenario_list.append(xosc_filename)
            else:
                catalog_content_tuples = self.extract_catalog_references(root_node)

                dir_name = os.path.dirname(xosc_filename)
                xosc_filename = xosc_filename.split("/")[-1]
                self.catalog_tuple_list += [
                    (xosc_filename, dir_name) + catalog_content_tuple
                    for catalog_content_tuple in catalog_content_tuples
                ]

    def extract_catalog_references(self, root_node):
        catalog_content_tuples = []
        catalog_elements = root_node.findall("Catalog")

        for catalog_element in catalog_elements:
            catalog_content_tuples += [
                (catalog_element.get("name"), child_element.get("name"))
                for child_element in catalog_element.getchildren()
            ]
        return catalog_content_tuples

