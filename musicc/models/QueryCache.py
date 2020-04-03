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
from musicc.models.MusiccScenario import MusiccScenario
from django.contrib.postgres.fields import ArrayField
from django.db import models
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.BaseModel import BaseModel
from django.contrib.auth import get_user_model
from musicc.models.Catalog import CatalogMapping

User = get_user_model()
from django.db.models.signals import post_save
import logging

logger = logging.getLogger("musicc")


class QueryCache(BaseModel):
    musicc_revision = models.ForeignKey("MusiccRevision", on_delete=models.CASCADE)
    query_string = models.TextField()
    results = models.ManyToManyField("MusiccScenario")

    @classmethod
    def create(cls, query_string, query_set, revision, user: User):
        query = cls(
            musicc_revision=MusiccRevision.active_objects.get(revision=revision),
            query_string=query_string,
            updated_by_user=user,
        )
        query.save()
        [query.results.add(result) for result in query_set]
        return query

    @classmethod
    def deactivate_cache(cls, **kwargs):
        cls.active_objects.all().delete()
        logger.info("Cache deactivated")

    def to_dict(self):
        data = {}
        data["Musicc"] = [
            "{0} - {1}".format(musicc.get_human_readable_id(), musicc.label) for musicc in self.results.all()
        ]

        data["OpenScenario"] = list(
            set(["{0}".format(musicc.scenario.get_human_readable_id()) for musicc in self.results.all()])
        )

        data["OpenDrive"] = list(
            set(["{0}".format(musicc.open_drive.get_human_readable_id()) for musicc in self.results.all()])
        )

        data["Catalogs"] = []
        for musicc in self.results.all():
            for catalog in musicc.scenario.catalog.all():
                data["Catalogs"].extend(
                    [
                        mapping.filename
                        for mapping in CatalogMapping.active_objects.filter(
                            catalog=catalog
                        )
                    ]
                )
        data["Catalogs"] = list(set(data["Catalogs"]))

        return data


post_save.connect(QueryCache.deactivate_cache, sender=MusiccScenario)
post_save.connect(QueryCache.deactivate_cache, sender=MusiccRevision)
