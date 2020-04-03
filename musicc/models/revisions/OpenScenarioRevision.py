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
from musicc.models.revisions.BaseRevision import BaseRevision
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.tools import get_file_hash
import datetime
from django.contrib.auth import get_user_model

User = get_user_model()



class OpenScenarioRevision(BaseRevision):

    revision_schema = {}
    root_node = "OpenSCENARIO"

    @classmethod
    def create(cls, file: UploadedFile, revision: str, user: User, active=False):
        revision_xsd = file.file.read()
        super().create(revision_xsd)

        file_hash = get_file_hash(revision_xsd)
        try:
            revision = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:
            revision = cls(
                revision=revision,
                description="desc",
                updated_by_user=user,
                revision_xsd=revision_xsd,
                file_hash=file_hash,
            )
            revision.save()
            if active:
                revision.activate()
        return revision
