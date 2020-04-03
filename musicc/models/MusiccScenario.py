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
from musicc.models.OpenScenario import OpenScenario
from musicc.models.OpenDrive import OpenDrive
from django.core.files.uploadedfile import UploadedFile
from musicc.models.Catalog import CatalogMapping
from musicc.utils.tools import get_file_hash
from musicc.utils.xml_functions import convert_xml_to_json
from musicc.models.revisions.MusiccRevision import MusiccRevision
from django.contrib.auth import get_user_model
from datetime import datetime
from musicc.models.Comment import CommentControl
from musicc.models.Tag import Tag
from musicc.models.Notification import Notification
from django.conf import settings
from musicc.models.IdPool import MusiccScenarioIdPool
from musicc.models.System import System

User = get_user_model()

from lxml.etree import DocumentInvalid, fromstring, Comment, tostring
from numpy.random import normal, uniform
import math
import numpy
from django.db.models import Max
import sys

import json
import logging
import uuid

logger = logging.getLogger("musicc")


class MusiccScenario(SynchronisableModel):
    version = models.IntegerField(null=True, blank=True)
    metadata = JSONField()
    musicc_blob = models.BinaryField()
    scenario_standard = models.CharField(max_length=10)
    scenario = models.ForeignKey("OpenScenario", on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    revision = models.ForeignKey(
        "MusiccRevision", on_delete=models.CASCADE, to_field="revision"
    )
    open_drive = models.ForeignKey("OpenDrive", on_delete=models.CASCADE)
    file_hash = models.CharField(max_length=500)
    estimated_size = models.PositiveIntegerField()
    images = models.ManyToManyField("ScenarioImage")
    resources = models.ManyToManyField("Resource", through="ResourceMapping")
    friendly_id = models.IntegerField()
    instance_prefix = models.CharField(max_length=1)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["version", "label", "revision"],
                condition=models.Q(active=True),
                name="only_one_active_musicc",
            )
        ]

    @classmethod
    def create(cls, file: UploadedFile, user: User, revision=None):
        musicc_file = file.file.read()
        musicc_json = convert_xml_to_json(musicc_file)

        musicc_file_as_etree = fromstring(musicc_file)
        musicc_file_header = musicc_file_as_etree.find("FileHeader")
        musicc_file_as_etree.remove(musicc_file_header)
        musicc_file_without_file_header = tostring(
            musicc_file_as_etree, encoding="utf-8"
        )

        musicc_revision = revision or MusiccRevision.latest_revision()
        file_hash = get_file_hash(musicc_file_without_file_header)

        try:
            latest_scenarios = cls.get_latest_scenarios(musicc_revision)

            musicc_scenario = latest_scenarios.get(file_hash=file_hash)
        except cls.DoesNotExist:
            open_scenario_file_id = musicc_json["MUSICCScenario"]["OpenSCENARIO"][
                "@filepath"
            ].split(".")[0]
            open_drive_file_id = musicc_json["MUSICCScenario"]["OpenDRIVE"][
                "@filepath"
            ].split(".")[0]

            label = musicc_json["MUSICCScenario"]["FileHeader"]["@label"]

            musicc_file_as_etree = fromstring(musicc_file)
            musicc_file_as_etree.xpath("//FileHeader")[0].set(
                "updateDateTime", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            )
            musicc_file_as_etree.xpath("//FileHeader")[0].set(
                "updateUsername", str(user)
            )

            musicc_file = tostring(
                musicc_file_as_etree, encoding="utf-8", xml_declaration=True
            )
            musicc_json = convert_xml_to_json(musicc_file)

            metadata = cls._create_json_metadata(musicc_json, revision)

            def sanitise_musicc_json(musicc_dict):
                for key, value in musicc_dict.items():
                    if isinstance(value, dict):
                        if "@value" in value and len(value.keys()) == 1:
                            musicc_dict[key] = value["@value"]
                        else:
                            sanitise_musicc_json(value)
                    elif isinstance(value, list):
                        for i, element in enumerate(value):
                            if "@value" in element and len(element.keys()) == 1:
                                value[i] = element["@value"]
                    elif key.startswith("@"):
                        musicc_dict[key[1:]] = value
                        del musicc_dict[key]

            sanitise_musicc_json(metadata)

            try:
                temp_custom_metadata = {
                    custom["@name"]: custom["@value"]
                    for custom in metadata["CustomMetadata"]["CustomTag"]
                }
                metadata["CustomMetadata"] = temp_custom_metadata
            except KeyError:
                pass

            open_scenario = OpenScenario.active_objects.filter(
                OpenScenario.query_from_human_readable_id(open_scenario_file_id)
            ).first()
            open_drive = OpenDrive.active_objects.filter(
                OpenDrive.query_from_human_readable_id(open_drive_file_id)
            ).first()

            musicc_scenario = cls(
                updated_by_user=user,
                metadata=metadata,
                scenario_standard="UN",
                scenario=open_scenario,
                label=label,
                revision=musicc_revision,
                open_drive=open_drive,
                musicc_blob=musicc_file,
                file_hash=file_hash,
                estimated_size=sys.getsizeof(musicc_file)
                + open_scenario.estimated_size
                + open_drive.estimated_size
                + sum(
                    [catalog.estimated_size for catalog in open_scenario.catalog.all()]
                ),
                active=False,
                friendly_id=MusiccScenarioIdPool.next_id(),
                instance_prefix=System.get_instance_prefix(),
            )
            musicc_scenario.save()
            # Auto-approve if:
            # - musicc_create does not require approveal
            # - superusers don't require approval and the user is a superuser
            if "musicc_create" not in settings.REQUIRES_APPROVAL or (
                not settings.ADMIN_REQUIRES_APPROVAL and user.is_superuser
            ):
                musicc_scenario.assign_new_version_number()
                musicc_scenario.active = True
                musicc_scenario.save()
        return musicc_scenario

    def _calculate_version_number(self):
        version = (
            int(
                self.__class__.objects.filter(
                    label=self.label, revision=self.revision
                ).aggregate(Max("version"))["version__max"]
                or self.get_probable_ancestor_version()
                or 0
            )
            + 1
        )
        return version

    def assign_new_version_number(self):
        self.version = self._calculate_version_number()
        # If we've labelled this as version 1 and we can't find the same label in another revision, this is new
        if self.version == 1 and not self.__class__.active_objects.filter(
            label=self.label
        ).exclude(revision=self.revision):
            Notification.notify_scenario_added(self)
        else:
            Notification.notify_favourite_updated(self)
        musicc_file_as_etree = fromstring(bytes(self.musicc_blob))
        musicc_file_as_etree.xpath("//FileHeader")[0].set("version", str(self.version))
        self.musicc_blob = tostring(
            musicc_file_as_etree, encoding="utf-8", xml_declaration=True
        )
        metadata = self.metadata
        metadata["version"] = self.version
        self.metadata = metadata
        self.save()

    def get_probable_ancestor_version(self):
        ancestor = (
            self.__class__.active_objects.filter(label=self.label)
            .exclude(revision__start_date=None)
            .exclude(
                revision__start_date__gt=(self.revision.start_date or datetime.max)
            )
            .order_by("-revision__start_date", "-version")
            .first()
        )
        if ancestor and ancestor.id != self.id:
            return ancestor.version - 1
        else:
            return None

    def _create_json_metadata(musicc_json, revision):

        from musicc.views.metadata import extract_musicc_json_schema

        metadata = musicc_json["MUSICCScenario"]["Metadata"]

        metadata = json.loads(json.dumps(metadata))
        metadata_schema = extract_musicc_json_schema(revision)

        for key, value in metadata.items():
            if (
                "array" in metadata_schema["properties"][key]
                and metadata_schema["properties"][key]["array"]
            ):
                if value:
                    inner_key = list(value.keys())[0]
                    inner_value = value[inner_key]
                    if not isinstance(inner_value, list):
                        metadata[key][inner_key] = [metadata[key][inner_key]]
                else:
                    metadata[key] = []

        header_data = musicc_json["MUSICCScenario"]["FileHeader"]
        file_header_data = {}
        for key, value in header_data.items():
            file_header_data[key[1:]] = {"@value": value}

        metadata.update(file_header_data)
        return metadata

    @classmethod
    def get_latest_scenarios(cls, revision=None):
        musicc_revision = revision or MusiccRevision.latest_revision()
        distinct_filter_set = (
            cls.active_objects.filter(revision=musicc_revision)
            .order_by("label", "-version")
            .distinct("label")
        )
        return cls.active_objects.filter(
            id__in=[entry.id for entry in distinct_filter_set]
        )
    
    ## Delete this scenario and any related files which aren't otherwise used
    #  @return The details of the deleted records
    def cascade_delete(self):
        deleted_records = {}
        # Delete any would-be orphans

        if MusiccScenario.active_objects.filter(scenario=self.scenario).count() <= 1:
            deleted_records["open_scenario"] = self.scenario.id
            deleted_records["catalogs"] = []
            for catalog in self.scenario.catalog.all():
                if CatalogMapping.active_objects.filter(catalog=catalog).count() <= 1:
                    deleted_records["catalogs"].append(catalog.id)
                    catalog.delete()
            self.scenario.delete()
        if (
            MusiccScenario.active_objects.filter(open_drive=self.open_drive).count()
            <= 1
        ):
            deleted_records["open_drive"] = self.open_drive.id
            self.open_drive.delete()

        deleted_records["musicc"] = self.id
        self.delete()

        # Create notifications for users who favourited this scenario 
        Notification.notify_favourite_deleted(self)
        return deleted_records

    ## Disallow new comments for this scenario
    def lock_comments(self, user):
        if not self.are_comments_locked():
            CommentControl.create(self, "LOCKED", user)

    ## Allow new comments for this scenario
    #  @return The results of the delete operation
    def unlock_comments(self):
        if self.are_comments_locked():
            return CommentControl.active_objects.get(
                state="LOCKED", label=self.label, revision=self.revision
            ).delete()

    ## Disable comments for this scenario
    #  @param user The user to whom the action will be attributed
    def disable_comments(self, user):
        if not self.are_comments_disabled():
            CommentControl.create(self, "DISABLED", user)

    ## Re-enable comments for this scenario
    #  @return The results of the delete operation
    def enable_comments(self):
        if self.are_comments_disabled():
            return CommentControl.active_objects.get(
                state="DISABLED", label=self.label, revision=self.revision
            ).delete()

    ## Check if a DISABLED CommentControl exists for this scenario
    #  @return The discovered CommentControl or false
    def are_comments_disabled(self):
        try:
            return CommentControl.active_objects.get(
                state="DISABLED", label=self.label, revision=self.revision
            )
        except CommentControl.DoesNotExist:
            return False

    ## Check if a LOCKED CommentControl exists for this scenario
    #  @return The discovered CommentControl or false
    def are_comments_locked(self):
        try:
            return CommentControl.active_objects.get(
                state="LOCKED", label=self.label, revision=self.revision
            )
        except CommentControl.DoesNotExist:
            return False

    ## Check if the specified user has created a 'favourite' tag for this scenario
    #  @param user The relevant user
    #  @return Whether a tag was found
    def is_favourited(self, user):
        return bool(
            Tag.active_objects.filter(
                musicc__label=self.label,
                musicc__revision=self.revision,
                updated_by_user=user,
                name="favourite",
            )
        )

    ## Get the human-friendly id combining the instance prefix and the int id
    #  @return The id
    def get_human_readable_id(self):
        return self.instance_prefix + str(self.friendly_id)

    ## Create a search query using the human readable id of a MUSICC record
    #  @param human_readable_id The id to search for 
    #  @return A Q object
    def query_from_human_readable_id(human_readable_id):
        instance_prefix = human_readable_id[0] if human_readable_id[0].isalpha() else ""
        if instance_prefix:
            human_readable_id = human_readable_id[1:]
        return Q(friendly_id=human_readable_id, instance_prefix=instance_prefix)

    def get_resources_file_size(self):
        return sum([resource.estimated_size for resource in self.resources.all()])

    def get_images_file_size(self):
        return sum([image.estimated_size for image in self.images.all()])
        
    ## Create a search query using the human readable id of an OpenScenario record
    #  @param human_readable_id The id to search for 
    #  @return A Q object
    def query_osc_from_human_readable_id(human_readable_id):
        instance_prefix = human_readable_id[0] if human_readable_id[0].isalpha() else ""
        if instance_prefix:
            human_readable_id = human_readable_id[1:]
        return Q(scenario__friendly_id=human_readable_id, scenario__instance_prefix=instance_prefix)

    ## Create a search query using the human readable id of an OpenDrive record
    #  @param human_readable_id The id to search for 
    #  @return A Q object
    def query_odr_from_human_readable_id(human_readable_id):
        instance_prefix = human_readable_id[0] if human_readable_id[0].isalpha() else ""
        if instance_prefix:
            human_readable_id = human_readable_id[1:]
        return Q(open_drive__friendly_id=human_readable_id, open_drive__instance_prefix=instance_prefix)
