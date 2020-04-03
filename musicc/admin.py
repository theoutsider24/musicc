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
from django.contrib import admin
from musicc.models.Organisation import Organisation
from musicc.models.logs.DownloadLog import DownloadLog
from musicc.models.logs.ChangeLog import ChangeLog
from musicc.models.Comment import Comment
from musicc.models.RegisteredSystem import RegisteredSystem
from musicc.models.System import System
from musicc.models.Profile import Profile
from musicc.models.Resource import Resource, ResourceMapping
from musicc.models.ScenarioImage import ScenarioImage

admin.site.register(Organisation)
admin.site.register(DownloadLog)
admin.site.register(ChangeLog)
admin.site.register(Comment)
admin.site.register(RegisteredSystem)
admin.site.register(System)
admin.site.register(Profile)
admin.site.register(ResourceMapping)
admin.site.register(Resource)
admin.site.register(ScenarioImage)