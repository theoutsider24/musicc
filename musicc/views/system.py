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
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from musicc.models.RegisteredSystem import RegisteredSystem
from musicc.models.System import System
from django.conf import settings

## Return the system screen
#  @param request Type: GET
#  @return A HTTP response with the rendered HTML
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@user_passes_test(lambda u: u.is_superuser)
def get_system_html(request):
    return render(
        request,
        "system/index.html",
        context={"system_details": System.get_system_settings(), "MASTER_HOST": settings.MASTER_HOST},
    )

## Send a registration token to register this system with its master
#  @param request Type: GET<br>
#                 parameter: token - The registration token
#                 parameter: instance_prefix - This system's desired system prefix
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@user_passes_test(lambda u: u.is_superuser)
def register_system_with_master(request):
    server_token = request.GET.get("token")
    instance_prefix = request.GET.get("instance_prefix")
    RegisteredSystem.register_with_master(instance_prefix, server_token)
    return HttpResponse(
        "Server registered with id {0}".format(System.get_system_settings().system_id)
    )

## Accepts system registrations
#  @param request Type: GET<br>
#                 parameter: token - A registration token
#  @return A HTTP response with the system's new id
def accept_instance_registration(request):
    token = request.GET.get("token")
    system_id = RegisteredSystem.register_new_instance(token)
    return HttpResponse(system_id)

## Generate a registration token for the current user
#  @param request Type: GET
#  @return A HTTP response with the token
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_registration_token(request):
    token = RegisteredSystem.generate_registration_token(request.user)
    return HttpResponse(token)

## Mark a registered system as inactive
#  @param request Type: GET<br>
#                 parameter: instance_id - The instance id of the system to deactivate
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def deactivate_system(request):
    instance_id = request.GET.get("instance_id")
    system = get_object_or_404(RegisteredSystem.active_objects, instance_id = instance_id, updated_by_user = request.user)
    system.delete()
    return HttpResponse("System has been deregistered")

## Re-activate a registered system
#  @param request Type: GET<br>
#                 parameter: instance_id - The instance id of the system to reactivate
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def reactivate_system(request):
    instance_id = request.GET.get("instance_id")
    system = get_object_or_404(RegisteredSystem.objects, active = False, instance_id = instance_id, updated_by_user = request.user)
    system.undelete()
    return HttpResponse("System has been reregistered")

## Get the systems which are registered to this system
#  @param request Type: GET<br>
#  @return A HTTP response with system information
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@user_passes_test(lambda u: u.is_superuser)
def get_registered_systems(request):
    data = [
        {
            "id": system.instance_id,
            "updated_by_user": system.updated_by_user.username,
            "organisation": system.updated_by_user.organisation_set.all()[0].name
            if system.updated_by_user.organisation_set.all()
            else "",
            "updated_date_time": system.updated_date_time,
            "active": system.active
        }
        for system in RegisteredSystem.objects.all()
        .order_by("-updated_date_time")
    ]

    return JsonResponse({"data": data})

## Get the registered systems belonging to the requesting user
#  @param request Type: GET<br>
#  @return A HTTP response with system information
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_my_registered_systems(request):
    data = [
        {
            "id": system.instance_id,
            "updated_by_user": system.updated_by_user.username,
            "organisation": system.updated_by_user.organisation_set.all()[0].name
            if system.updated_by_user.organisation_set.all()
            else "",
            "updated_date_time": system.updated_date_time,
            "active": system.active
        }
        for system in RegisteredSystem.objects.filter(updated_by_user=request.user)
        .order_by("-updated_date_time")
    ]

    return JsonResponse({"data": data})