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
from musicc.models.BaseModel import BaseModel
from django.contrib.auth.models import User
from django.db import models
import logging
logger = logging.getLogger("musicc")

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, to_field="username", null=True, blank=True, related_name="profile")
    has_agreed = models.BooleanField(default=False)

    @classmethod
    def create(cls, user, has_agreed):
        profile = cls(user=user, has_agreed=has_agreed)
        profile.save()
        return profile

    def update_all_users(has_agreed, ignore_users_with_agreements=False):
        """ Updates all users without agreements or with agreements"""
        user_list = [users for users in User.objects.all()]
        count=0
        if ignore_users_with_agreements == True:
            for user in user_list:
                if user.profile.first() == None:
                    count = count+1
                    Profile.create(user=user, has_agreed=has_agreed)

        else:
            for user in user_list:
                if user.profile.first() == None:
                    Profile.create(user=user, has_agreed=has_agreed)
                    count = count+1
                else:
                    profile = user.profile.first()
                    profile.has_agreed = has_agreed
                    profile.save()
                    count = count+1
        logger.info('Successfully updated {0} user agreements'.format(count))
        return user_list
        

    def __str__(self):
        return (
            self.user.username
            + " - "
            + str(self.has_agreed)
        )