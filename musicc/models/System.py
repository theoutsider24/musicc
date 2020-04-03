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
from django.core.validators import RegexValidator
import uuid

class System(models.Model):
   single_upper_alphabetic_validator = RegexValidator(r'^[A-Z]{1}$', 'Only upper case alphabetic characters are allowed.')

   name = models.CharField(max_length=8, primary_key=True)
   system_id = models.UUIDField(primary_key=False, editable=False, unique=True)
   instance_prefix = models.CharField(max_length=1, validators=[single_upper_alphabetic_validator])
   registration_time = models.DateTimeField(auto_now_add=True)
   
   @classmethod
   def register(cls, instance_prefix, system_id):
      system_settings = cls(name="SETTINGS", instance_prefix=instance_prefix, system_id = system_id)
      system_settings.save()
      return system_settings

   def register_as_master():
      System.register("M", uuid.uuid4() .hex)

   @classmethod
   def get_system_settings(cls):
      try:
         return cls.objects.get(pk="SETTINGS")
      except cls.DoesNotExist:
         return None


   def get_instance_prefix():
      try:
         return System.get_system_settings().instance_prefix
      except:
         raise Exception("System has not been registered")
   
   def __str__(self):
      return "{0} - {1} - {2}".format(self.instance_prefix, self.system_id, self.registration_time)