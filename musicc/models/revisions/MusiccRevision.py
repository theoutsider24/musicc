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
import os
import io
from musicc.models.revisions.BaseRevision import BaseRevision
from django.db import models
from musicc.models.revisions.OpenDriveRevision import OpenDriveRevision
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.tools import get_file_hash
import datetime
from django.contrib.auth import get_user_model
import zipfile
from django.conf import settings
from musicc.models.Notification import Notification

User = get_user_model()


class MusiccRevision(BaseRevision):
    open_drive_revision = models.ForeignKey(
        "OpenDriveRevision", on_delete=models.CASCADE
    )
    open_scenario_revision = models.ForeignKey(
        "OpenScenarioRevision", on_delete=models.CASCADE
    )
    root_node = "MUSICCScenario"
    revision_schema = {}

    @classmethod
    def create(cls, file: UploadedFile, revision: str, user: User, active=False):
        revision_xsd = file.file.read()
        super().create(revision_xsd)

        file_hash = get_file_hash(revision_xsd)
        try:
            musicc_scenario_revision = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:

            musicc_scenario_revision = cls(
                revision=revision,
                description="desc",
                updated_by_user=user,
                open_drive_revision=OpenDriveRevision.latest_revision(),
                open_scenario_revision=OpenScenarioRevision.latest_revision(),
                revision_xsd=revision_xsd,
                file_hash=file_hash,
            )
            musicc_scenario_revision.save()
            if active:
                musicc_scenario_revision.activate()
        return musicc_scenario_revision

    def activate(self):
        self.open_drive_revision.activate()
        self.open_scenario_revision.activate()
        super(MusiccRevision, self).activate()
        Notification.notify_revision_activation(self)

    def get_combined_zip(self):
        target_file_path = os.path.join(
            settings.DOWNLOAD_DIR, "musicc_{0}.zip".format(self.revision)
        )
        with zipfile.ZipFile(
            target_file_path, mode="w", compression=zipfile.ZIP_STORED
        ) as combined_zip:
            self._write_schema_file(
                combined_zip, self, "musicc_{0}".format(self.revision)
            )
            self._write_schema_file(
                combined_zip,
                self.open_scenario_revision,
                "openScenario_{0}".format(self.open_scenario_revision.revision),
            )
            self._write_schema_file(
                combined_zip,
                self.open_drive_revision,
                "openDrive_{0}".format(self.open_drive_revision.revision),
            )

        return target_file_path

    def _write_schema_file(
        self, zip_file: zipfile.ZipFile, revision: BaseRevision, file_name
    ):
        if zipfile.is_zipfile(io.BytesIO(revision.revision_xsd)):
            file_extension = ".zip"
            data = bytes(revision.revision_xsd)
        else:
            file_extension = ".xsd"
            data = bytes(revision.revision_xsd).decode("utf-8")

        zip_file.writestr("{0}{1}".format(file_name, file_extension), data)

