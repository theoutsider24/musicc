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
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Q
from musicc.models.BaseModel import BaseModel, ActiveManager, SynchronisableModel
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.xml_functions import convert_xml_to_json, load_xsd_from_blob
from musicc.models.revisions.OpenDriveRevision import OpenDriveRevision
from musicc.models.IdPool import OpenDriveIdPool
from musicc.utils.tools import get_file_hash
import sys
from django.contrib.auth import get_user_model
from musicc.models.System import System

User = get_user_model()

from lxml import etree

import logging


logger = logging.getLogger("musicc")


class OpenDrive(SynchronisableModel):
    metadata = JSONField()
    open_drive_blob = models.BinaryField()
    sim_3d_type = models.CharField(max_length=50)
    sim_id = models.IntegerField()
    version = models.CharField(max_length=10)
    revision = models.ForeignKey(
        "OpenDriveRevision", on_delete=models.CASCADE, to_field="revision"
    )
    file_hash = models.CharField(max_length=500)
    estimated_size = models.PositiveIntegerField()
    friendly_id = models.IntegerField()
    instance_prefix = models.CharField(max_length=1)

    @classmethod
    def create(cls, file: UploadedFile, user: User, revision=None):
        open_drive_file = file.file.read()

        open_drive_json = convert_xml_to_json(open_drive_file)

        open_drive_revision = revision or OpenDriveRevision.latest_revision()

        file_hash = get_file_hash(open_drive_file)

        try:
            open_drive = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:
            open_drive = cls(
                updated_by_user=user,
                metadata=open_drive_json["OpenDRIVE"]["header"],
                open_drive_blob=open_drive_file,
                revision=open_drive_revision,
                version="ver1",
                sim_id=1,
                file_hash=file_hash,
                estimated_size=sys.getsizeof(open_drive_file),
                friendly_id=OpenDriveIdPool.next_id(),
                instance_prefix=System.get_instance_prefix()
            )
            open_drive.save()
        return open_drive

    def get_human_readable_id(self):
        return self.instance_prefix + str(self.friendly_id)

    def query_from_human_readable_id(human_readable_id):
        instance_prefix = human_readable_id[0] if human_readable_id[0].isalpha() else ""
        if instance_prefix:
            human_readable_id = human_readable_id[1:]
        return Q(friendly_id=human_readable_id, instance_prefix=instance_prefix)
