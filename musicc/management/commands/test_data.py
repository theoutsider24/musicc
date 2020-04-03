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
from django.core.management.base import BaseCommand
from musicc.utils.ZipSummary import ZipSummary
from musicc.models.revisions.MusiccRevision import MusiccRevision
import os
import zipfile
import shutil
import random
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.MusiccRecordBuilder import MusiccRecordBuilder
from PIL import Image, ImageDraw
from musicc.tests.utilities import initialise_super_user
from lxml import etree

from django.contrib.auth import get_user_model

User = get_user_model()

import logging

logger = logging.getLogger("musicc")


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            "-d", "--dir", type=str, help="Directory to create test data variations"
        )
        parser.add_argument(
            "-t", "--test", type=str, help="Folder to hold test data zips"
        )

    def handle(self, *args, **options):

        self.dir = options["dir"]
        self.test_data_dir = options["test"]
        self.good_data_copy_dir = self.dir + "_copy"

        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
        
        self.copy_xsds()  
        
        self.create_main_scenario_zip("master_scenarios")


        self.create_missing_xosc_zip("test_scenarios_missing_xosc")
        self.create_random_image_file_zip("test_scenarios_random_image")
        self.create_extra_image_zip("test_scenarios_extra_image")


    def create_main_scenario_zip(self, zip_name):

        try:
            self.copy_good_data()

            self.create_zip(
                self.good_data_copy_dir,
                os.path.join(self.test_data_dir, zip_name),
                zip_name,
            )

        except FileExistsError:
            self.clean_on_file_exists()
        finally:
            self.final_removal_of_copied_dir()

    def create_missing_xosc_zip(self, zip_name):
        tmp_zip_name = zip_name + "_tmp"

        try:
            self.copy_good_data()

            tmp_zip_location = os.path.join(self.test_data_dir, tmp_zip_name)

            self.create_zip(
                self.good_data_copy_dir,
                tmp_zip_location,
                zip_name,
            )
            with open(tmp_zip_location + ".zip","rb") as file:
                zip_summary = ZipSummary(UploadedFile(file=file, name=zip_name + ".zip"))

                file_to_remove = random.choice(zip_summary.open_scenario_list)
                os.remove(os.path.join(self.good_data_copy_dir, file_to_remove))

                self.create_zip(
                    self.good_data_copy_dir,
                    os.path.join(self.test_data_dir, zip_name),
                    zip_name,
                )

            os.remove(tmp_zip_location + ".zip")

        except FileExistsError:

            self.clean_on_file_exists()
        finally:
            self.final_removal_of_copied_dir()

    def create_random_image_file_zip(self, zip_name):

        images_dir = os.path.join(self.good_data_copy_dir, "Images")
    
        try:
            self.copy_good_data()
           
            if os.path.exists(images_dir):
                img = Image.new("RGB", (60, 30), color="red")
                img.save(os.path.join(images_dir, "new_img.png"))
                shutil.copy(
                    os.path.join(images_dir, "new_img.png"),
                    os.path.join(images_dir, "new_img.jkh"),
                )
                os.remove(os.path.join(images_dir, "new_img.png"))

                self.create_zip(
                    self.good_data_copy_dir,
                    os.path.join(self.test_data_dir, zip_name),
                    zip_name,
                )

        except FileExistsError:
            self.clean_on_file_exists()
        finally:
            self.final_removal_of_copied_dir()

    def create_extra_image_zip(self, zip_name):

        images_dir = os.path.join(self.good_data_copy_dir, "Images")

        try:
            self.copy_good_data()
            if os.path.exists(images_dir):

                img = Image.new("RGB", (60, 30), color="red")
                img.save(os.path.join(images_dir, "random.png"))

                self.create_zip(
                    self.good_data_copy_dir,
                    os.path.join(self.test_data_dir, zip_name),
                    zip_name,
                )
        except FileExistsError:
            self.clean_on_file_exists()
        finally:
            self.final_removal_of_copied_dir()

    def create_zip(self, base_dir, new_zip, zip_name):
        shutil.make_archive(new_zip, "zip", base_dir)

    def copy_good_data(self):
        shutil.copytree(os.path.join(self.dir, "Scenarios"), self.good_data_copy_dir, ignore=shutil.ignore_patterns("generated.zip", "generated", "xsd"))

    def copy_xsds(self):
        shutil.copytree(os.path.join(self.dir, "xsd"), self.test_data_dir)


    def clean_on_file_exists(self):
        shutil.rmtree(self.good_data_copy_dir)
        shutil.rmtree(self.test_data_dir)
        os.mkdir(self.test_data_dir)

    def final_removal_of_copied_dir(self):
        shutil.rmtree(self.good_data_copy_dir)


