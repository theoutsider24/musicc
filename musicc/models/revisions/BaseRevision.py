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
import abc
from django.utils import timezone
from musicc.utils.xml_functions import load_xsd_from_blob


class BaseRevision(SynchronisableModel):
    revision = models.CharField(max_length=31, unique=True)
    description = models.CharField(max_length=255)
    start_date = models.DateTimeField(null=True, blank=True, default=None)
    revision_xsd = models.BinaryField()
    file_hash = models.CharField(max_length=500)

    class Meta:
        abstract = True
        ordering = ["-updated_date_time"]

    @classmethod
    def latest_revision(cls):
        return cls.active_objects.exclude(start_date=None).latest("start_date")

    def activate(self):
        if not self.start_date:
            self.start_date = timezone.now()
            self.save()

    @classmethod
    def is_valid_schema(cls, file):
        try:
            load_xsd_from_blob(file, cls.root_node)
        except Exception as e:
            raise Exception("{0} XSD is not a valid schema".format(cls.__name__))

    @classmethod
    def create(cls, file):
        cls.is_valid_schema(file)