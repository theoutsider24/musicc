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
from musicc.models.BaseModel import SynchronisableModel
from django.core.files import File
from musicc.utils.tools import get_file_hash
from django.contrib.auth import get_user_model
import sys
User = get_user_model()


class Resource(SynchronisableModel):
    estimated_size = models.PositiveIntegerField()
    file = models.FileField()
    file_hash = models.CharField(max_length=500)

    @classmethod
    def create(cls, uploaded_file: File, user: User):        
        file_content = uploaded_file.file.read()
        uploaded_file.file.seek(0)
        file_hash = get_file_hash(file_content)
        try:
            resource_file = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:
            resource_file = cls(
                estimated_size=uploaded_file.size,
                file=uploaded_file,
                file_hash=file_hash,
                updated_by_user=user,
            )
            resource_file.save()

        return resource_file

    def should_be_synchronised(self):
        return self.musiccscenario_set.filter(active=True).exists()

class ResourceMapping(SynchronisableModel):
    musicc = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE)
    resource = models.ForeignKey("Resource", on_delete=models.CASCADE)
    filename = models.CharField(max_length=500)
    directory = models.CharField(max_length=500)

    @classmethod
    def create(cls, uploaded_file: File, musicc, user: User):
        resource = Resource.create(uploaded_file, user)
        filename = uploaded_file.name
        directory = ""


        # Do we already have a link between the MUSICC and the resource but with a different filename?
        # - If so remove it [File has been renamed]
        try:
            cls.active_objects.filter(musicc=musicc, resource=resource).exclude(filename=filename).delete()
        except cls.DoesNotExist:
            pass

        # Do we already have a link between the MUSICC and a different resource with the same filename?
        # - If so remove it [File has been updated]
        try:
            cls.active_objects.filter(musicc=musicc, filename=filename).exclude(resource=resource).delete()
        except cls.DoesNotExist:
            pass
            
        resource_mapping = cls.active_objects.get_or_create(resource=resource, musicc=musicc, filename=filename, directory=directory, defaults={'updated_by_user': user})
        return resource_mapping

    def should_be_synchronised(self):
        return self.musicc.active and self.resource.active

