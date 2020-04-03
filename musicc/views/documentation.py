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
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.static import serve
import mimetypes
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings


DOCUMENTATION_ROOT = "index.html"

## Returns the MKDocs documentation html for debug mode
#  @param request Type: GET<br>
#  @param path The target path (after ../docs/) from the url 
#  @return A HTTP response with the served documentation or an error if not in DEBUG mode
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def documentation(request, path):
    if path == "":
        path = DOCUMENTATION_ROOT
    path = "docs/" + path
    if not settings.DOCUMENTATION_ACCESS_FUNCTION(request.user):
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
    if settings.DEBUG:
        return serve(request, path, settings.DOCUMENTATION_HTML_ROOT)
    else:
        return Http404(
            "Documentation should be served statically via your web server when debug is False"
        )
    return response

