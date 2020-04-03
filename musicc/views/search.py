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
from django.shortcuts import render
from musicc.utils.queries import QueryParser
from django.contrib.auth import get_user_model
import json
import difflib
from rolepermissions.checkers import has_role

User = get_user_model()

from django.http import (
    JsonResponse,
    HttpResponse,
    FileResponse,
    Http404,
    HttpResponseBadRequest,
    HttpResponseServerError,
)
from musicc.models.Comment import Comment, CommentControl
from musicc.models.Tag import Tag
from musicc.models.MusiccScenario import MusiccScenario
from musicc.models.QueryCache import QueryCache
from musicc.models.logs.DownloadLog import DownloadLog
from musicc.views import curation
from musicc.models.logs.ChangeLog import ChangeLog
import shutil
from django.conf import settings
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from musicc.models.QueryCache import QueryCache
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.views.metadata import extract_musicc_json_schema
from musicc.views.tooltips import tooltips
from musicc.utils.tools import unique, order_query_set


from django.core.paginator import Paginator
from django.db.models import Sum
from datetime import datetime
from django.shortcuts import get_object_or_404

import logging

logger = logging.getLogger("musicc")

## Return the search screen
#  @param request Type: GET
#  @return A HTTP response with the rendered HTML
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def search(request):
    # Passing the tokeniserRegex allows for Javascript to use the same regex as Python for parsing query tokens 
    return render(
        request,
        "search/index.html",
        context={
            "tokeniserRegex": QueryParser.regex.replace("\\", "\\\\\\"),
            "tooltips": tooltips,
        },
    )

## Return the profile screen
#  @param request Type: GET
#  @return A HTTP response with the rendered HTML
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def profile(request):
    return render(
        request,
        "profile/index.html",
        context={
            "revisions": [
                revision.revision
                for revision in MusiccRevision.active_objects.exclude(
                    start_date=None
                ).order_by("-start_date")
            ],
            "tooltips": tooltips,
        },
    )

## Return the detail screen for the specified scenario
#  @param request Type: POST<br>
#                 parameter: id - The human-readable id of the scenario
#  @return A HTTP response with the rendered HTML
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def detail(request):
    id = request.POST.get("id")
    # Detect and separate the instance prefix
    instance_prefix = id[0] if id[0].isalpha() else ""
    if instance_prefix:
        id = id[1:]

    # Begin construction of the context dict which will be passed to the template
    context = {}
    context["musicc"] = get_object_or_404(MusiccScenario.active_objects, friendly_id=id, instance_prefix=instance_prefix)
    context["organisation"] = (
        context["musicc"].updated_by_user.organisation_set.all()[0].name
        if context["musicc"].updated_by_user.organisation_set.all()
        else ""
    )

    revision_numbers = unique(
        [
            musicc_record.revision.revision
            for musicc_record in MusiccScenario.active_objects.filter(
                label=context["musicc"].label
            )
            .exclude(revision__start_date=None)
            .order_by("-revision__start_date")
        ]
    )

    context["history"] = [
        {
            "version": musicc_record.version,
            "mus": musicc_record.get_human_readable_id(),
            "osc": musicc_record.scenario.get_human_readable_id(),
            "odr": musicc_record.open_drive.get_human_readable_id(),
            "time": musicc_record.updated_date_time,
            "user": musicc_record.updated_by_user,
        }
        for musicc_record in MusiccScenario.active_objects.filter(
            label=context["musicc"].label, revision=context["musicc"].revision
        ).order_by("-version")
    ]
    # Remove osc/odr data where the osc/odr was not changed from one version to the next
    for i in range(len(context["history"]) - 1):
        j = i + 1
        higher_version = context["history"][i]
        lower_version = context["history"][j]
        if higher_version["osc"] == lower_version["osc"]:
            higher_version.pop("osc", None)
        if higher_version["odr"] == lower_version["odr"]:
            higher_version.pop("odr", None)

    context["versions"] = [
        musicc_record.version
        for musicc_record in MusiccScenario.active_objects.filter(
            label=context["musicc"].label, revision=context["musicc"].revision
        )
        .order_by("-version")
        .exclude(version=context["musicc"].version)
    ]

    context["osc_versions"] = [
        musicc_record.version
        for musicc_record in MusiccScenario.active_objects.filter(
            label=context["musicc"].label, revision=context["musicc"].revision
        )
        .exclude(version=context["musicc"].version)
        .exclude(scenario__id=context["musicc"].scenario.id)
        .order_by("scenario__id", "-version")
        .distinct("scenario__id")
    ]

    context["odr_versions"] = [
        musicc_record.version
        for musicc_record in MusiccScenario.active_objects.filter(
            label=context["musicc"].label, revision=context["musicc"].revision
        )
        .exclude(version=context["musicc"].version)
        .exclude(open_drive__id=context["musicc"].open_drive.id)
        .order_by("open_drive__id", "-version")
        .distinct("open_drive__id")
    ]

    context["revisions"] = [
        {
            "revision": revision,
            "id": MusiccScenario.active_objects.filter(
                label=context["musicc"].label, revision=revision
            )
            .order_by("-version")[0]
            .get_human_readable_id(),
        }
        for revision in revision_numbers
    ]

    context["musicc_file"] = (
        bytes(context["musicc"].musicc_blob).decode("utf-8").strip()
    )
    context["osc_file"] = (
        bytes(context["musicc"].scenario.open_scenario_blob).decode("utf-8").strip()
    )
    context["odr_file"] = (
        bytes(context["musicc"].open_drive.open_drive_blob).decode("utf-8").strip()
    )

    context["metadata"] = json.dumps(context["musicc"].metadata)

    context["comments_disabled"] = context["musicc"].are_comments_disabled()
    context["comments_locked"] = context["musicc"].are_comments_locked()

    # If the user is a moderator, display all comments
    # Otherwise only display active comments
    if has_role(request.user, "moderator"):
        context["comments"] = [
            comment
            for comment in Comment.objects.filter(
                musicc__label=context["musicc"].label,
                musicc__revision=context["musicc"].revision,
            ).order_by("-updated_date_time")
        ]
    else:
        context["comments"] = [
            comment
            for comment in Comment.active_objects.filter(
                musicc__label=context["musicc"].label,
                musicc__revision=context["musicc"].revision,
            ).order_by("-updated_date_time")
        ]

    context["tags"] = [
        tag.name
        for tag in Tag.active_objects.filter(
            musicc__label=context["musicc"].label,
            musicc__revision=context["musicc"].revision,
            updated_by_user=request.user,
        ).order_by("updated_date_time")
    ]
    context["favourite"] = bool(context["tags"] and "favourite" in context["tags"])
    if context["favourite"]:
        context["tags"].remove("favourite")

    context["enabled_features"] = settings.ENABLED_FEATURES.copy()

    context["next_revision"] = (
        MusiccScenario.active_objects.filter(
            label=context["musicc"].label,
            revision__start_date__gt=context["musicc"].revision.start_date,
        )
        .order_by("revision__start_date", "-version")
        .first()
    )
    context["previous_revision"] = (
        MusiccScenario.active_objects.filter(
            label=context["musicc"].label,
            revision__start_date__lt=context["musicc"].revision.start_date,
        )
        .order_by("-revision__start_date", "-version")
        .first()
    )

    # If the target revision doesn't support GlobalTags, disable all tagging
    if (
        "tagging" in context["enabled_features"]
        and "GlobalTags"
        not in extract_musicc_json_schema(context["musicc"].revision)["properties"]
    ):
        context["enabled_features"].remove("tagging")

    context["images"] = [i.image for i in context["musicc"].images.all()]

    context["resources"] = [m.filename for m in context["musicc"].resourcemapping_set.filter(active=True)]

    return render(request, "search/detail/container.html", context=context)

## Return a unified diff of specific file types between two MUSICC versions
#  @param request Type: GET<br>
#                 parameter: label - The target MUSICC label
#                 parameter: v1 - Source MUSICC version
#                 parameter: v2 - Target MUSICC version
#                 parameter: revision - The target MUSICC revision
#                 parameter: file_type - The file_type in question ['mus','odr','osc']
#  @return A HTTP response with a multi-line string in unified diff format
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def diff_version(request):
    label = request.GET.get("label")
    v1 = request.GET.get("v1")
    v2 = request.GET.get("v2")
    revision = request.GET.get("revision")
    file_type = request.GET.get("file_type")

    version = [v1, v2]

    musicc_files = [
        MusiccScenario.active_objects.get(
            label=label, version=version, revision=revision
        )
        for version in version
    ]

    if file_type == "mus":
        comparison_string_lines = [
            bytes(musicc_file.musicc_blob).decode("utf-8").strip().splitlines()
            for musicc_file in musicc_files
        ]
    elif file_type == "odr":
        comparison_string_lines = [
            bytes(musicc_file.open_drive.open_drive_blob)
            .decode("utf-8")
            .strip()
            .splitlines()
            for musicc_file in musicc_files
        ]
    elif file_type == "osc":
        comparison_string_lines = [
            bytes(musicc_file.scenario.open_scenario_blob)
            .decode("utf-8")
            .strip()
            .splitlines()
            for musicc_file in musicc_files
        ]

    diff = difflib.unified_diff(
        comparison_string_lines[0],
        comparison_string_lines[1],
        "version {0}".format(musicc_files[0].version),
        "version {0}".format(musicc_files[1].version),
        musicc_files[0].updated_date_time.strftime("%m/%d/%Y, %H:%M:%S"),
        musicc_files[1].updated_date_time.strftime("%m/%d/%Y, %H:%M:%S"),
    )
    lines = []
    for line in diff:
        lines.append(line)
    return HttpResponse("\n".join(lines))

## Generate a unified diff of two musicc blobs
#  @param from_blob The previous version of the blob
#  @param to_blob The new version of the blob
#  @param from_blob_name The name of the previous blob
#  @param to_blob_name The name of the new blob
#  @param from_blob_date The date of the previous version's creation
#  @param to_blob_date The date of the new version's creation
#  @return A multi-line string in unified diff format
def _get_unified_diff_of_blobs(
    from_blob, to_blob, from_blob_name, to_blob_name, from_blob_date, to_blob_date
):
    diff = difflib.unified_diff(
        _blob_to_lines_array(from_blob),
        _blob_to_lines_array(to_blob),
        from_blob_name,
        to_blob_name,
        from_blob_date,
        to_blob_date,
    )
    lines = []
    for line in diff:
        lines.append(line)
    return "\n".join(lines)

## Converts a blob to a list of utf-8 -decoded strings where each element is one line
#  @param blob The blob to be converted
#  @return A list of strings
def _blob_to_lines_array(blob):
    return bytes(blob).decode("utf-8").strip().splitlines()

## Gets a list of unified diffs for a particular ChangeLog entry
#  @param request Type: GET<br>
#                 parameter: id - The ID of the ChangeLog
#  @return A HTTP response with a list of unified diffs
def diff_change_logs(request):
    change = get_object_or_404(ChangeLog, pk=request.GET.get("id"))
    diffs = []
    # This function only returns diffs for MUSICC records

    # For each MUSICC associated with the ChangeLog entry
    for musicc in [mapping.record for mapping in change.changemusiccmapping_set.all()]:
        # If there are other MUSICC entries with the same label and revision
        if MusiccScenario.active_objects.filter(
            label=musicc.label, revision=musicc.revision
        ).exclude(pk=musicc.id).exists():
            # If the scenario has been approved and assigned a version number 
            if musicc.version:
                # Get the scenario with the next highest version number
                # TODO Should this include a revision=musicc.revision filter?
                most_recent_musicc = (
                    MusiccScenario.active_objects.filter(label=musicc.label)
                    .filter(version__lt=musicc.version)
                    .order_by("version")
                    .last()
                )
            else:
                # Get the top level scenario with the same label
                most_recent_musicc = MusiccScenario.get_latest_scenarios(
                    revision=musicc.revision
                ).get(label=musicc.label)
            # Generate unified diffs
            diffs.append(
                _get_unified_diff_of_blobs(
                    most_recent_musicc.musicc_blob,
                    musicc.musicc_blob,
                    "{0} - Version {1}".format(
                        most_recent_musicc.label, most_recent_musicc.version
                    ),
                    "New version",
                    most_recent_musicc.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S"),
                    change.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S"),
                )
            )
        # If the scenario is brand new, create diff against empty string
        else:
            diffs.append(
                _get_unified_diff_of_blobs(
                    "".encode("utf-8"),
                    musicc.musicc_blob,
                    "",
                    "New file",
                    "",
                    change.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S"),
                )
            )

    return JsonResponse({"diffs": diffs})


@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def release_notes(request):
    return render(request, "release-notes.html")

## Get the scenarios matching a query
#  @param query_string The query to execute
#  @param revision The target revision
#  @param user The user to whom the query will be attributed
#  @return A queryset with matching MUSICC scenarios
def get_query_results(query_string, revision, user):
    query_as_q_object = QueryParser(query_string).evaluate(user, revision)
    return MusiccScenario.get_latest_scenarios(revision).filter(query_as_q_object)


@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def query(request):
    user = User.objects.get(username=request.user)
    try:
        query_string = request.GET.get("query", "")
        page_length = int(request.GET.get("page_length", -1))
        page_number = int(request.GET.get("page_number", 0))

        order_column = request.GET.get("order_column", "id")
        order_direction = request.GET.get("order_direction", "asc")
        revision = request.GET.get(
            "musicc_revision", MusiccRevision.latest_revision().revision
        )

        if order_direction == "desc":
            order_direction = "-"
        else:
            order_direction = ""

        bypass_cache = "Tags__Tag" in query_string

        if bypass_cache:
            is_already_cached = False
        else:
            is_already_cached = QueryCache.active_objects.filter(
                query_string=query_string, musicc_revision__revision=revision
            ).exists()

        musicc_scenario_highest_versions = MusiccScenario.get_latest_scenarios(revision)
        if is_already_cached:
            cached_query = QueryCache.active_objects.filter(
                query_string=query_string, musicc_revision__revision=revision
            ).first()

            query_set = cached_query.results.all()
            query_id = cached_query.id
        else:
            query_set = get_query_results(query_string, revision, request.user)
            cached_query = QueryCache.create(query_string, query_set, revision, user)

        query_set = cached_query.results.all()
        query_id = cached_query.id

        total_estimated_size = sum([result.estimated_size for result in query_set])
        resources_estimated_size = sum([result.get_resources_file_size() for result in query_set])
        images_estimated_size = sum([result.get_images_file_size() for result in query_set])
        records_filtered = query_set.count()
        count = musicc_scenario_highest_versions.count()

        query_set = order_query_set(query_set, order_direction, order_column)

        if page_length > 0:
            paginator = Paginator(query_set.all(), page_length)
            query_set = paginator.get_page(page_number)

        metadata = [
            {
                "id": result.get_human_readable_id(),
                "uid": result.id,
                "metadata": result.metadata,
                "comments": 0
                if result.are_comments_disabled()
                else Comment.active_objects.filter(
                    musicc__label=result.label, musicc__revision=result.revision
                ).count(),
                "broken": False
                if result.are_comments_disabled()
                else Comment.active_objects.filter(
                    scenario_broken=True, musicc=result
                ).exists(),
                "favourited": result.is_favourited(request.user),
            }
            for result in query_set
        ]

        for meta in metadata:
            user_tags = [
                tag.name
                for tag in Tag.active_objects.filter(
                    musicc__label=meta["metadata"]["label"],
                    musicc__revision__revision=meta["metadata"]["revision"],
                    updated_by_user=request.user,
                ).order_by("-updated_date_time")
            ]
            if "GlobalTags" in meta["metadata"]:
                meta["metadata"]["Tags"] = meta["metadata"].pop("GlobalTags")
            elif user_tags:
                meta["metadata"]["Tags"] = {}

            if user_tags:
                meta["metadata"]["Tags"]["UserTag"] = user_tags

            musicc_record = MusiccScenario.active_objects.get(
                    label=meta["metadata"]["label"],
                    revision__revision=meta["metadata"]["revision"],
                    version=meta["metadata"]["version"])
            meta["metadata"]["MUSICC_ID"] = musicc_record.get_human_readable_id()
            meta["metadata"]["OpenScenario_ID"] = musicc_record.scenario.get_human_readable_id()
            meta["metadata"]["OpenDrive_ID"] = musicc_record.open_drive.get_human_readable_id()

        logger.info(
            "[User:{0}] {1} results found for query string [{2}] query_id [{3}] - cached={4}".format(
                request.user,
                records_filtered,
                query_string,
                query_id,
                is_already_cached,
            )
        )
        return JsonResponse(
            {
                "recordsTotal": count,
                "recordsFiltered": records_filtered,
                "estimatedDownloadSize": total_estimated_size or 0,
                "estimatedResourcesSize": resources_estimated_size or 0,
                "estimatedImagesSize": images_estimated_size or 0,
                "results": metadata,
                "query_id": query_id,
            }
        )
    except Exception as e:
        logger.exception(
            "[User:{0}] Query [{1}] was unsuccessful - {2}".format(
                request.user, query_string, str(e)
            )
        )
        return HttpResponseBadRequest("Invalid query format")
