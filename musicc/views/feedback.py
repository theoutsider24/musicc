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
from musicc.models.MusiccScenario import MusiccScenario
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from musicc.models.Comment import Comment
from musicc.models.Tag import Tag
from django.http import HttpResponse, HttpResponseBadRequest
from rolepermissions.decorators import has_role_decorator
from musicc.views.decorators import require_feature_enabled

## Add a comment to a MUSICC scenario
#  @param request Type: GET<br>
#                 parameter: id - The UUID of the MUSICC scenario<br>
#                 parameter: comment - The comment to be added<br>
#                 parameter: is_broken[optional] - [default:"false"] Whether the comment is reporting a broken scenario
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@require_feature_enabled("comments")
def add_comment(request):
    musicc_id = request.GET.get("id")
    comment_string = request.GET.get("comment")
    is_broken = request.GET.get("is_broken", "false").lower() == "true"

    if comment_string:
        musicc = MusiccScenario.active_objects.get(pk=musicc_id)
        if not musicc.are_comments_disabled() and not musicc.are_comments_locked():
            # Always apply comments to the latest version of a scenario
            latest_musicc = MusiccScenario.active_objects.filter(
                label=musicc.label, revision=musicc.revision
            ).order_by("-version")[0]
            Comment.create(comment_string, latest_musicc, request.user, is_broken)
            return HttpResponse("success")
        elif musicc.are_comments_disabled():
            return HttpResponseBadRequest("Commenting on this thread is disabled")
        elif musicc.are_comments_locked():
            return HttpResponseBadRequest("Commenting on this thread is locked")
    
    return HttpResponseBadRequest("No comment string provided")

@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("moderator")
@require_feature_enabled("comments")
def delete_comment(request):
    comment_id = request.GET.get("id")
    Comment.active_objects.get(pk = comment_id).delete()
    return HttpResponse("success")

@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("moderator")
@require_feature_enabled("comments")
def undelete_comment(request):
    comment_id = request.GET.get("id")
    Comment.objects.get(pk = comment_id).undelete()
    return HttpResponse("success")

@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("moderator")
@require_feature_enabled("comments")
def lock_comments(request):
    musicc_id = request.GET.get("id")
    musicc = MusiccScenario.active_objects.get(pk=musicc_id)
    musicc.lock_comments(request.user)
    return HttpResponse("success")


@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("moderator")
@require_feature_enabled("comments")
def disable_comments(request):
    musicc_id = request.GET.get("id")
    musicc = MusiccScenario.active_objects.get(pk=musicc_id)
    musicc.disable_comments(request.user)
    return HttpResponse("success")

@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("moderator")
@require_feature_enabled("comments")
def enable_comments(request):
    musicc_id = request.GET.get("id")
    musicc = MusiccScenario.active_objects.get(pk=musicc_id)
    musicc.enable_comments()
    return HttpResponse("success")

@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("moderator")
@require_feature_enabled("comments")
def unlock_comments(request):
    musicc_id = request.GET.get("id")
    musicc = MusiccScenario.active_objects.get(pk=musicc_id)
    musicc.unlock_comments()
    return HttpResponse("success")

## Add a tag to a MUSICC scenario
#  @param request Type: GET<br>
#                 parameter: id - The UUID of the MUSICC scenario<br>
#                 parameter: tag - The tag to be added
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@require_feature_enabled("tagging")
def add_tag(request):
    musicc_id = request.GET.get("id")
    tag_string = request.GET.get("tag")

    musicc = MusiccScenario.active_objects.get(pk=musicc_id)
    # Check if the same tag has been added to another version of the same musicc file under this revision
    if not Tag.active_objects.filter(musicc__label = musicc.label, musicc__revision = musicc.revision, updated_by_user = request.user, name = tag_string):
        Tag.create(tag_string, musicc, request.user)
        return HttpResponse("success")
    else:
        return HttpResponseBadRequest("Duplicate tag")

@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@require_feature_enabled("tagging")
def remove_tag(request):
    musicc_id = request.GET.get("id")
    tag_string = request.GET.get("tag")

    musicc = MusiccScenario.active_objects.get(pk=musicc_id)
    
    Tag.active_objects.get(name = tag_string, musicc__label = musicc.label, musicc__revision = musicc.revision, updated_by_user = request.user).delete()
    return HttpResponse("success")