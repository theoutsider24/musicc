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
import uuid

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.db import models

from musicc.models.BaseModel import BaseModel
from musicc.models.System import System
from datetime import datetime

User = get_user_model()


class RegisteredSystem(BaseModel):
    instance_id = models.UUIDField(primary_key=False, unique=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    ## Create a token using the user id and a generated instance id
    #  @param user The user requesting the registration
    #  @return The token
    def generate_registration_token(user):
        instance_id = uuid.uuid4().hex
        token = signing.dumps((user.username, instance_id))
        return token

    ## Accept and decode a token and register the requesting system
    #  @param token The registration token
    #  @return The assigned instance id
    def register_new_instance(token):
        username, instance_id = signing.loads(token, max_age=3600)
        system = RegisteredSystem(
            updated_by_user=User.objects.get(username=username), 
            instance_id=instance_id,
            last_sync = datetime.utcfromtimestamp(0)
        )
        system.save()
        return instance_id
    
    ## Send registration request to the master system with the provided registration token
    #  @param instance_prefix The desired instance prefix
    #  @param token The registration token
    #  @return The assigned system id
    def register_with_master(instance_prefix, token):
        response = requests.get(
            settings.MASTER_HOST + "/register_system", params={"token": token}
        )
        if response.status_code == requests.codes.ok:
            system_id = response.text
            System.register(instance_prefix, system_id)
            return system_id
        else:
            raise Exception(response.text)

    def __str__(self):
        return "{0} - {1} - {2}".format(self.updated_by_user, self.instance_id, self.updated_date_time)