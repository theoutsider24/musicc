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
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from musicc.models.Notification import Notification



## Get a page of paginated notifications
#  @param request Type: GET<br>
#                 parameter: page[optional] - [default:1] The page number of notificatins to retrieve
#  @return A HTTP response with the notifications
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_notifications(request):
    page = int(request.GET.get("page", 1))
    notifications = Notification.get_user_notifications(request.user, page)
    notification_information = {
        "notifications": [
            {
                "message": notification.message,
                "seen": notification.seen,
                "date": notification.updated_date_time,
            }
            for notification in notifications
        ],
        "page": page,
        "lastPage": not notifications.has_next(),
    }
    # Mark notifications as seen once we've transferred them
    for notification in notifications:
        notification.seen = True
        notification.save()
    return JsonResponse(notification_information)
