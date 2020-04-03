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
from musicc.models.BaseModel import BaseModel, SynchronisableModel
from django.core.files.uploadedfile import UploadedFile
from musicc.utils.xml_functions import convert_xml_to_json, load_xsd_from_blob
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from musicc.models.IdPool import OpenScenarioIdPool
from musicc.utils.tools import get_file_hash
import sys
from io import BytesIO
from django.contrib.auth import get_user_model
from musicc.models.System import System

User = get_user_model()

from lxml import etree
import logging


logger = logging.getLogger("musicc")


class OpenScenario(SynchronisableModel):
    metadata = JSONField()
    open_scenario_blob = models.BinaryField()
    revision = models.ForeignKey(
        "OpenScenarioRevision", on_delete=models.CASCADE, to_field="revision"
    )
    version = models.CharField(max_length=10)
    catalog = models.ManyToManyField("Catalog", through="CatalogMapping")
    file_hash = models.CharField(max_length=500)
    estimated_size = models.PositiveIntegerField()
    friendly_id = models.IntegerField()
    instance_prefix = models.CharField(max_length=1)

    @classmethod
    def create(cls, file: UploadedFile, user: User, catalog_id_list, revision=None):
        open_scenario_file = file.file.read()

        open_scenario_json = convert_xml_to_json(open_scenario_file)

        open_scenario_revision = revision or OpenScenarioRevision.latest_revision()

        file_hash = get_file_hash(open_scenario_file + bytes(catalog_id_list, "utf8"))

        try:
            open_scenario = cls.active_objects.get(file_hash=file_hash)
        except cls.DoesNotExist:
            open_scenario = cls(
                updated_by_user=user,
                metadata=open_scenario_json["OpenSCENARIO"]["FileHeader"],
                open_scenario_blob=open_scenario_file,
                revision=open_scenario_revision,
                version="ver1",
                file_hash=file_hash,
                estimated_size=sys.getsizeof(open_scenario_file),
                friendly_id=OpenScenarioIdPool.next_id(),
                instance_prefix=System.get_instance_prefix(),
            )
            open_scenario.save()
        return open_scenario

    @classmethod
    def validate(cls, revision, file, root_type=None):

        xml_etree = etree.parse(BytesIO(file))
        xml_root = xml_etree.getroot()

        param_values_dict = {
            element.get("name"): element.get("value")
            for element in xml_etree.xpath("//Parameter")
        }

        for key, value in param_values_dict.items():
            for elem in xml_root.iter():
                if (any(key in s for s in elem.items())) and (elem.tag != "Parameter"):
                    for elem_key in elem.keys():
                        if elem.get(elem_key) == key:
                            elem.set(elem_key, value)

        file = bytes(etree.tostring(xml_root))

        super(OpenScenario, cls).validate(revision, file, root_type)

    def get_human_readable_id(self):
        return self.instance_prefix + str(self.friendly_id)

    def query_from_human_readable_id(human_readable_id):
        instance_prefix = human_readable_id[0] if human_readable_id[0].isalpha() else ""
        if instance_prefix:
            human_readable_id = human_readable_id[1:]
        return Q(friendly_id=human_readable_id, instance_prefix=instance_prefix)
