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
from django.core.files import File
from musicc.utils.tools import get_file_hash
from io import BytesIO
from musicc.models.BaseModel import SynchronisableModel
from django.contrib.auth import get_user_model
User = get_user_model()
import sys
import os

class ScenarioImage(SynchronisableModel):
    file_type = models.CharField(max_length=25)
    estimated_size = models.PositiveIntegerField()
    image = models.ImageField()
    file_hash = models.CharField(max_length=500)

    @classmethod
    def create(cls, uploaded_image: File, user: User):

        file_extension = os.path.splitext(uploaded_image.name)[1][1:]

        image = uploaded_image.file.read()
        file_hash = get_file_hash(image)

        image_file = File(BytesIO(image))
        image_file.name = uploaded_image.name

        try:
            scenario_image = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:
            scenario_image = cls(
                file_type=file_extension,
                estimated_size=image_file.size,
                image=image_file,
                file_hash=file_hash,
                updated_by_user=user,
            )
            scenario_image.save()
        
        return scenario_image

    def should_be_synchronised(self):
        return self.musiccscenario_set.filter(active=True).exists()