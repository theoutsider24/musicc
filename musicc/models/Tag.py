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
from musicc.models.BaseModel import BaseModel
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(BaseModel):
    name = models.CharField(max_length=256)
    musicc = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE)

    def __str__(self):
        return (
            self.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S")
            + " - "
            + self.updated_by_user.username
            + " - "
            + self.name
        )

    @classmethod
    def create(cls, name, musicc, user):
        tag = cls(musicc=musicc, name=name, updated_by_user=user)
        tag.save()
        return tag

    def get_users_who_favourited(musicc, user_to_exclude=None):
        return User.objects.filter(
            id__in=[
                tag.updated_by_user.id
                for tag in Tag.active_objects.filter(
                    musicc__label=musicc.label,
                    musicc__revision=musicc.revision,
                    name="favourite",
                )
            ]
        )
