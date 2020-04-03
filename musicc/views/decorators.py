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
from django.conf import settings
from functools import wraps
from django.http import HttpResponseNotAllowed
from django.utils.log import log_response

## Decorator to check if a named feature is present in the list of enabled features
#  @param feature the The feature name
#  @return A HTTP error message if the feature is not enabled
def require_feature_enabled(feature):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if feature not in settings.ENABLED_FEATURES:
                response = HttpResponseNotAllowed("Feature not enabled: {0}".format(feature))
                log_response(
                    'Feature not enabled (%s): %s', feature, request.path,
                    response=response,
                    request=request,
                )
                return response
            return func(request, *args, **kwargs)
        return inner
    return decorator

## Decorator to check if user has agreed to terms and conditions
#  @param user the The fuser
# Used with 'user_passes_test'
def user_agreed_t_and_c_check(user):
    try:
        has_agreed = user.profile.first().has_agreed
    except:
        has_agreed = False
    return has_agreed
    