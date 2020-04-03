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
from musicc.models.Notification import Notification

class Comment(BaseModel):
    message = models.CharField(max_length=256)
    musicc = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE)
    scenario_broken = models.BooleanField(default=False)

    def __str__(self):
        return (
            self.musicc.label
            + " - "
            + self.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S")
            + " - "
            + self.updated_by_user.username
            + " - "
            + self.message
        )

    @classmethod
    def create(cls, comment_string, musicc, user, scenario_broken):
        comment = cls(musicc=musicc, message=comment_string, updated_by_user=user, scenario_broken=scenario_broken)
        comment.save()
        Notification.notify_comment_on_favourite(comment)
        return comment

class CommentControl(BaseModel):
    revision = models.ForeignKey("MusiccRevision", on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    state = models.CharField(
        choices=(("LOCKED", "LOCKED"), ("DISABLED", "DISABLED")), max_length=16
    )

    @classmethod
    def create(cls, musicc, state, user):
        cls.active_objects.filter(revision=musicc.revision, label=musicc.label).delete()
        comment_control = cls(state = state, revision=musicc.revision, label=musicc.label, updated_by_user=user)
        comment_control.save()
        return comment_control