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
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

from musicc.utils.xml_functions import load_xsd_from_blob, validate_xml_against_xsd
from lxml import etree
from django.db.models.query import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class CustomQuerySet(QuerySet):
    def delete(self):
        self.update(active=False)

    def undelete(self):
        self.update(active=True)

    def active(self):
        return self.filter(active=True)


class ActiveManager(models.Manager):
    def get_queryset(self):
        return CustomQuerySet(self.model, using=self._db).active()

class DefaultManager(models.Manager):
    def get_queryset(self):
        return CustomQuerySet(self.model, using=self._db)


class BaseModel(models.Model):

    updated_date_time = models.DateTimeField(auto_now_add=True)
    updated_by_user = models.ForeignKey(
        User, on_delete=models.CASCADE, to_field="username", null=True, blank=True
    )
    active = models.BooleanField(default=True)

    objects = DefaultManager()
    active_objects = ActiveManager()

    class Meta:
        abstract = True

    @classmethod
    def validate(cls, revision, file, root_type=None):

        if revision.revision_schema.get(revision.id) == None:
            schema = load_xsd_from_blob(revision, root_type=root_type)
            revision.revision_schema[revision.id] = schema
        validate_xml_against_xsd(file, revision.revision_schema[revision.id])

    def delete(self):
        self.active = False
        self.save()

    def undelete(self):
        self.active = True
        self.save()

    @receiver(pre_delete)
    def delete_intercept(sender, instance, **kwargs):
        instance.active = False
        instance.save()


class SynchronisableModel(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True

    def should_be_synchronised(self):
        # Override this in child classes to apply extra rules to determine if an object should be synced
        return True