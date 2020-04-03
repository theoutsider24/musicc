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
from django.shortcuts import render, redirect
from django.conf import settings
import datetime
from musicc.models.revisions.OpenDriveRevision import OpenDriveRevision
from musicc.models.revisions.OpenScenarioRevision import OpenScenarioRevision
from musicc.models.revisions.MusiccRevision import MusiccRevision
from lxml.etree import fromstring, tostring, _Comment
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rolepermissions.checkers import has_role

from django.core.files.uploadedfile import UploadedFile
from io import BytesIO
from musicc.models.OpenDrive import OpenDrive
from musicc.models.OpenScenario import OpenScenario
from musicc.models.MusiccScenario import MusiccScenario
from musicc.models.Resource import Resource, ResourceMapping

from musicc.models.logs.ChangeLog import (
    ChangeLog,
    ChangeCatalogMapping,
    ChangeMusiccMapping,
    ChangeOpenDriveMapping,
    ChangeOpenScenarioMapping,
)
from musicc.models.ApprovalRequest import ApprovalRequest

from musicc.models.logs.DownloadLog import DownloadLog

import os, sys
from django.http import Http404, HttpResponse, JsonResponse
from musicc.models.QueryCache import QueryCache
import hashlib
from musicc.utils.xml_functions import convert_xml_to_json
from musicc.utils.tools import get_file_hash
from django.http import Http404, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

User = get_user_model()

from rolepermissions.decorators import has_role_decorator
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from musicc.utils.ZipSummary import ZipSummary
from musicc.utils.MusiccRecordBuilder import MusiccRecordBuilder

import copy
import logging

logger = logging.getLogger("musicc")


@require_POST
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def upload_revisions(request):
    try:
        if (
            "open_scenario_xsd" in request.FILES
            and request.POST["open_scenario_rev_id"]
        ):
            OpenScenarioRevision.create(
                request.FILES["open_scenario_xsd"],
                request.POST["open_scenario_rev_id"],
                request.user,
                True,
            )

        if "open_drive_xsd" in request.FILES and request.POST["open_drive_rev_id"]:
            OpenDriveRevision.create(
                request.FILES["open_drive_xsd"],
                request.POST["open_drive_rev_id"],
                request.user,
                True,
            )

        if "musicc_xsd" in request.FILES and request.POST["musicc_rev_id"]:
            MusiccRevision.create(
                request.FILES["musicc_xsd"], request.POST["musicc_rev_id"], request.user
            )

        logger.info(
            "[User:{0}] Uploaded revisions {1}".format(request.user, request.FILES)
        )
        return HttpResponse("Files uploaded succesfully")
    except Exception as e:
        logger.exception(
            "[User:{0}] Failed to upload revisions [{1}] : {2}".format(
                request.user, request.FILES, str(e)
            )
        )
        return HttpResponseServerError(str(e))


@require_POST
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def upload_zip(request):
    revision = request.POST.get("revision")
    validate_only = request.POST.get("validate_only", "false").lower() == "true"
    try:
        if "file_ingestion_zip" in request.FILES:
            zip_summary = ZipSummary(request.FILES["file_ingestion_zip"])
            musicc_builder = MusiccRecordBuilder(zip_summary, request.user, revision)
            if not validate_only:
                musicc_builder.process_musicc_files()
                musicc_builder.musicc_context.change_log.create_approval_request(
                    request.user
                )
            else:
                musicc_builder.validate()
            return (
                JsonResponse(
                    {"errors": musicc_builder.musicc_context.error_list}, status=500
                )
                if musicc_builder.musicc_context.error_list
                else HttpResponse(
                    "Zip {0} succesfully".format(
                        "validated" if validate_only else "uploaded"
                    )
                )
            )
        else:
            return HttpResponseServerError("Zip-file not present")
    except Exception as e:
        logger.exception(
            "Failed {0}".format("validation" if validate_only else "upload")
        )
        return HttpResponseServerError(str(e))


## Return the curator screen
#  @param request Type: POST
#  @return A HTTP response with the rendered HTML
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def get_curation_html(request):
    return render(request, "curation/index.html")

## Get the details of all MUSICC revisions
#  @param request Type: GET
#  @return A HTTP response with revision details
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_revision_info(request):
    musicc_revisions = MusiccRevision.active_objects.all()
    musicc_revision_info = [
        {
            "mus_rev": revision.revision,
            "odr_rev": revision.open_drive_revision.revision,
            "osc_rev": revision.open_scenario_revision.revision,
            "start_date": revision.start_date,
            "scenario_count": "{0} ({1})".format(
                MusiccScenario.active_objects.filter(revision=revision).count(),
                MusiccScenario.get_latest_scenarios(revision).count(),
            ),
        }
        for revision in musicc_revisions
    ]
    if not musicc_revision_info:
        return HttpResponseServerError("No musicc revisions found")
    return JsonResponse({"results": musicc_revision_info})

## Activates a MUSICC revision
#  @param request Type: GET<br>
#                 parameter: revision - The MUSICC revision to be activated
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def activate_revision(request):
    revision = request.GET.get("revision")

    if not revision:
        return HttpResponseBadRequest("No revision given")

    try:
        # Get the target revision
        revision_to_activate = MusiccRevision.active_objects.get(revision=revision)
        # Only activate the revision if it has some active musicc records
        if MusiccScenario.active_objects.filter(revision=revision).count() > 0:
            revision_to_activate.activate()
            logger.info(
                "[User:{0}] Revision {1} activated".format(request.user, revision)
            )
            return HttpResponse("Revision {0} activated succesfully".format(revision))
        else:
            return HttpResponseServerError(
                "Revision {} cannot be activated without any associated musicc scenarios".format(
                    revision
                )
            )
    except Exception as e:
        logger.exception(
            "[User:{0}] Revision [{1}] was not activated".format(
                request.user, revision, str(e)
            )
        )
        return HttpResponseBadRequest(
            "Revision [{0}] was not activated".format(revision)
        )

## Get the details of all changes
#  @param request Type: GET
#  @return A HTTP response with change log details
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def get_change_log(request):
    data = [
        {
            "id": record.id,
            "type": record.change_type,
            "revertedBy": record.reverted_by.id if record.reverted_by else None,
            "updated_date_time": record.updated_date_time,
            "updated_by_user": record.updated_by_user.username,
            "musicc_revision": record.musicc_revision.revision,
        }
        # Exclude logs which were not or have not yet been applied
        for record in ChangeLog.active_objects.exclude(
            approvalrequest__status__in=["DENIED", "CANCELLED", "PENDING"]
        ).order_by("-updated_date_time")
    ]

    return JsonResponse({"data": data})

## Get the details of all approval requests
#  @param request Type: GET
#  @return A HTTP response with approval queue details
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def get_approval_queue(request):
    data = [
        {
            "id": record.change.id,
            "request_id": record.id,
            "type": record.change.change_type,
            "updated_date_time": record.updated_date_time,
            "submitted_by": record.submitted_by.username,
            "musicc_revision": record.change.musicc_revision.revision,
            # A status of None will prompt the display of Approve or Reject buttons
            "status": record.status
            if record.submitted_by == request.user or record.status != "PENDING"
            else None,
        }
        for record in ApprovalRequest.active_objects.all().order_by(
            "-updated_date_time"
        )
    ]

    return JsonResponse({"data": data})

## Get the details of all approval requests submitted by the requesting user
#  @param request Type: GET
#  @return A HTTP response with approval queue details
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_submissions_queue(request):
    data = [
        {
            "id": record.change.id,
            "request_id": record.id,
            "type": record.change.change_type,
            "updated_date_time": record.updated_date_time,
            "submitted_by": record.submitted_by.username,
            "reviewed_by": record.reviewed_by.username if record.reviewed_by else "-",
            "musicc_revision": record.change.musicc_revision.revision,
            "status": record.status,
        }
        for record in ApprovalRequest.active_objects.filter(
            change__updated_by_user=request.user
        ).order_by("-updated_date_time")
    ]

    return JsonResponse({"data": data})

## Approve an appoval request
#  @param request Type: GET<br>
#                 parameter: id - The ID of the approval request
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def approve_change(request):
    request_id = request.GET.get("id")
    approval_request = get_object_or_404(ApprovalRequest.active_objects, pk=request_id)
    approval_request.approve(request.user)
    return HttpResponse("Change approved")

## Reject an appoval request
#  @param request Type: GET<br>
#                 parameter: id - The ID of the approval request
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def reject_change(request):
    request_id = request.GET.get("id")
    approval_request = get_object_or_404(ApprovalRequest.active_objects, pk=request_id)
    approval_request.reject(request.user)
    return HttpResponse("Change rejected")

## Get the details of the modified files for a specific change
#  @param request Type: GET
#                 parameter: id - The ID of a change log
#  @return A HTTP response with details of the change
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_change_summary(request):
    change_id = request.GET.get("id")
    change = get_object_or_404(ChangeLog.active_objects, pk=change_id)
    # If the user is not a curator, they may only see their own changes
    if (
        not has_role(request.user, "curator")
        and not change.updated_by_user == request.user
    ):
        raise PermissionDenied

    data = {}
    data["Musicc"] = [
        "#{0} {1} - version {2}".format(
            musicc_mapping.record.get_human_readable_id(),
            musicc_mapping.record.label,
            musicc_mapping.record.version,
        )
        for musicc_mapping in ChangeMusiccMapping.active_objects.filter(
            change_log=change
        )
    ]

    data["OpenScenario"] = [
        "{0}".format(
            open_scenario_mapping.filename
            or open_scenario_mapping.record.get_human_readable_id()
        )
        for open_scenario_mapping in ChangeOpenScenarioMapping.active_objects.filter(
            change_log=change
        ).distinct("filename")
    ]

    data["OpenDrive"] = [
        "{0}".format(
            open_drive_mapping.filename
            or open_drive_mapping.record.get_human_readable_id()
        )
        for open_drive_mapping in ChangeOpenDriveMapping.active_objects.filter(
            change_log=change
        ).distinct("filename")
    ]

    data["Catalogs"] = [
        "{0}".format(
            catalog_mapping.filename or catalog_mapping.record.get_human_readable_id()
        )
        for catalog_mapping in ChangeCatalogMapping.active_objects.filter(
            change_log=change
        ).distinct("filename")
    ]

    return JsonResponse({"data": data})

## Get the details of all downloads
#  @param request Type: GET
#  @return A HTTP response with download log details
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def get_download_log(request):
    data = [record.to_dict() for record in DownloadLog.active_objects.all()]

    return JsonResponse({"data": data})

## Get the files which were included in a specific
#  @param request Type: GET
#                 parameter: id - A download id
#  @return A HTTP response with the details of the download
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def get_download_summary(request):
    download_id = request.GET.get("id")
    query = DownloadLog.active_objects.get(pk=download_id).query

    return JsonResponse({"data": query.to_dict()})

# These tags cannot be edited through the browser
uneditable_musicc_tags = [
    "FileHeader",
    "OpenSCENARIO",
    "OpenDRIVE",
    "ThreeDimensionalModels",
]


## Retrieve the MUSICC text which can be edited in-browser
#  @param request Type: GET<br>
#                 parameter: id - The UUID of the MUSICC scenario
#  @return A HTTP response with the editable text
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def get_editable_musicc(request):
    musicc_id = request.GET.get("id")

    blob = bytes(MusiccScenario.active_objects.get(id=musicc_id).musicc_blob)
    blob = fromstring(blob)

    # Remove all uneditable fields
    for field in uneditable_musicc_tags:
        element = blob.find(field)
        if element is not None:
            blob.remove(element)

    blob_without_file_header = tostring(blob)
    return HttpResponse(bytes(blob_without_file_header))


## Take an edited version of a MUSICC file and validate it
#  @param request Type: POST<br>
#                 parameter: id - The UUID of the MUSICC scenario<br>
#                 parameter: content - The edited content
#  @return A HTTP response with a message indicating the validity of the content
@require_POST
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def validate_musicc_from_editor(request):
    musicc_id = request.POST.get("id")
    musicc_edited_content = request.POST.get("content")

    original_musicc_record = MusiccScenario.active_objects.get(id=musicc_id)
    original_blob = fromstring(bytes(original_musicc_record.musicc_blob))
    try:
        edited_blob = fromstring(musicc_edited_content)
        new_blob = _get_proposed_new_musicc_blob(original_blob, edited_blob)
    except Exception as e:
        return HttpResponseServerError(e)

    try:
        MusiccScenario.validate(original_musicc_record.revision, tostring(new_blob))
    except Exception as e:
        return HttpResponseServerError(e)

    return HttpResponse("Valid")

## Take an edited version of a MUSICC file and apply the edits
#  @param request Type: POST<br>
#                 parameter: id - The UUID of the MUSICC scenario<br>
#                 parameter: content - The edited content
#  @return A HTTP response with a message indicating the operation's success
@require_POST
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def apply_musicc_edit(request):

    musicc_id = request.POST.get("id")
    musicc_edited_content = request.POST.get("content")

    # Get both the original and edited blobs as etrees and calculate the resulting etree
    original_musicc_record = MusiccScenario.active_objects.get(id=musicc_id)
    original_blob = fromstring(bytes(original_musicc_record.musicc_blob))
    try:
        edited_blob = fromstring(musicc_edited_content)
        new_blob = _get_proposed_new_musicc_blob(original_blob, edited_blob)
    except Exception as e:
        return HttpResponseServerError(e)

    # Create a new MUSICC record using a file-like version of the new etree
    new_record = MusiccScenario.create(
        UploadedFile(
            file=BytesIO(tostring(new_blob, encoding="utf-8", xml_declaration=True)),
            name="",
        ),
        request.user,
        original_musicc_record.revision,
    )
    # Copy all image and resource mappings to the new version
    new_record.images.add(*original_musicc_record.images.all())
    for resource_mapping in original_musicc_record.resourcemapping_set.filter(
        active=True
    ):
        new_resource = ResourceMapping(
            resource=resource_mapping.resource,
            musicc=new_record,
            filename=resource_mapping.filename,
            directory=resource_mapping.directory,
            updated_by_user=resource_mapping.updated_by_user,
        )
        new_resource.save()

    # If a new version has been created, create a change log and approval request
    if new_record.id != original_musicc_record.id:
        message = "Update succesful, id: {0}.".format(
            new_record.get_human_readable_id()
        )
        change_log = ChangeLog.create("CREATE", request.user, new_record.revision)
        ChangeMusiccMapping.create(change_log=change_log, musicc=new_record)
        change_log.create_approval_request(request.user)
    else:
        if new_record.label == original_musicc_record.label:
            message = "Content matched version {0}, no update was performed.".format(
                new_record.version
            )
        else:
            message = "Content matched version {0} of {1}, no update was preformed.".format(
                new_record.version, new_record.label
            )

    return HttpResponse(message)


## Given two musicc etrees, one original and one edited, calculate and apply the differences to create a new modified etree
#  @param original_blob The original unedited data as an lxml etree
#  @param edited_blob The edited data as an lxml etree
#  @return The resulting etree
def _get_proposed_new_musicc_blob(original_blob, edited_blob):
    # The top level tag must remain unchanged
    if edited_blob.tag != original_blob.tag:
        raise Exception("Top level tag must be {0}".format(original_blob.tag))

    # Get all of the second-level tags from the original data excluding comments
    original_element_tags = [
        element.tag
        for element in list(original_blob)
        if not isinstance(element, _Comment)
    ]

    # Get all of the second-level tags from the edited data excluding comments, uneditable tags and tags which didn't exist in the original
    edited_element_tags = [
        element.tag
        for element in list(edited_blob)
        if not isinstance(element, _Comment)
        and not element.tag in uneditable_musicc_tags
        and element.tag in original_element_tags
    ]

    # Get any tags which appeared in the original but don't appear in the edited version (excluding uneditable tags)
    deleted_tags = (
        set(original_element_tags)
        - set(edited_element_tags)
        - set(uneditable_musicc_tags)
    )

    # Copy original to avoid unintended modifications
    new_blob = copy.deepcopy(original_blob)

    # Replace all edited tags with their new versions
    for tag in edited_element_tags:
        original_tag = new_blob.find(tag)
        edited_tag = edited_blob.find(tag)
        new_blob.replace(original_tag, edited_tag)

    # Remove all deleted tags
    for tag in deleted_tags:
        original_tag = new_blob.find(tag)
        new_blob.remove(original_tag)

    return new_blob
