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
from django.db import models
from musicc.models.BaseModel import BaseModel, SynchronisableModel
from django.contrib.auth import get_user_model
User = get_user_model()

from django.core.files.uploadedfile import UploadedFile
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from musicc.models.OpenScenario import OpenScenario
from musicc.utils.tools import get_file_hash
import sys
import zipfile



class Catalog(SynchronisableModel):
    catalog_blob = models.BinaryField()
    revision = models.ForeignKey("OpenScenarioRevision", on_delete=models.CASCADE)
    estimated_size = models.PositiveIntegerField()
    file_hash = models.CharField(max_length=500)


    @classmethod
    def create(cls, file: UploadedFile, user: User):

        catalog_file = file.file.read()

        open_scenario_revision = OpenScenarioRevision.latest_revision()

        file_hash = get_file_hash(catalog_file)
        try:
            catalog = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:

            catalog = cls(
                catalog_blob=catalog_file,
                revision=open_scenario_revision,
                estimated_size=sys.getsizeof(catalog_file),
                file_hash=file_hash,
                updated_by_user=user,

            )
            catalog.save()
        return catalog
           


class CatalogMapping(SynchronisableModel):
    open_scenario = models.ForeignKey("OpenScenario", on_delete=models.CASCADE)
    catalog = models.ForeignKey("Catalog", on_delete=models.CASCADE)
    filename = models.CharField(max_length=500)
    directory = models.CharField(max_length=500)
    catalog_type = models.CharField(max_length=500)

    @classmethod
    def create(cls, open_scenario: OpenScenario, catalog_tuple, base_directory = ""):

        catalog = catalog_tuple[0]
        filename = catalog_tuple[1][0]
        directory = catalog_tuple[1][1].replace(base_directory, "")
        catalog_type = catalog_tuple[1][2]

        catalog_mapping = cls.active_objects.get_or_create(open_scenario=open_scenario, catalog=catalog, filename=filename, directory=directory, catalog_type=catalog_type)

        return catalog_mapping
    
    def should_be_synchronised(self):
        return self.open_scenario.active and self.catalog.active
