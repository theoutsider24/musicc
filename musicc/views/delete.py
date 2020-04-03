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
from rolepermissions.decorators import has_role_decorator
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, HttpResponse, JsonResponse
from musicc.models.logs.ChangeLog import (
    ChangeLog,
    ChangeMusiccMapping,
    ChangeOpenDriveMapping,
    ChangeOpenScenarioMapping,
    ChangeCatalogMapping,
)
from musicc.models.OpenScenario import OpenScenario
from musicc.models.OpenDrive import OpenDrive
from musicc.models.Catalog import Catalog
from musicc.views.search import get_query_results
from musicc.models.revisions.MusiccRevision import MusiccRevision


## Delete MUSICC records matching the provided query
#  @param request Type: GET<br>
#                 parameter: query_string - The query string
#                 parameter: revision - The target MUSICC revision
#  @return A HTTP response with the number of records deleted
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def delete_musicc(request):
    user = request.user
    query_string = request.GET.get("query_string")
    musicc_revision = request.GET.get("revision")
    change_log = None

    # Get the initial set of scenarios to delete
    matching_records = get_query_results(query_string, musicc_revision, request.user)

    # Repeatedly execute the query to ensure all matching scenarios are deleted
    while matching_records:
        # If we haven't already, create a changelog to cover these deletions
        if not change_log:
            change_log = ChangeLog.create(
                "DELETE",
                user,
                MusiccRevision.active_objects.get(revision=musicc_revision),
            )
        # Perform the deletion
        perform_logged_deletion(matching_records, change_log)
        # Check if there are more matching scenarios
        matching_records = get_query_results(
            query_string, musicc_revision, request.user
        )

    return HttpResponse(matching_records.count())


def perform_logged_deletion(records, change_log):
    for musicc_record in records:
        deletion_summary = musicc_record.cascade_delete()
        ChangeMusiccMapping.create(change_log=change_log, musicc=musicc_record)
        if "open_drive" in deletion_summary:
            ChangeOpenDriveMapping.create(
                change_log=change_log,
                open_drive=OpenDrive.objects.get(pk=deletion_summary["open_drive"]),
                musicc=musicc_record,
            )
        if "open_scenario" in deletion_summary:
            ChangeOpenScenarioMapping.create(
                change_log=change_log,
                open_scenario=OpenScenario.objects.get(
                    pk=deletion_summary["open_scenario"]
                ),
                musicc=musicc_record,
            )

            if "catalogs" in deletion_summary:
                for catalog in deletion_summary["catalogs"]:
                    ChangeCatalogMapping.create(
                        change_log=change_log,
                        catalog=Catalog.objects.get(pk=catalog),
                        musicc=musicc_record,
                    )


@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def revert_change(request):
    user = request.user
    id = request.GET.get("id")

    original_change_log = ChangeLog.active_objects.get(pk=id)
    
    # Create record of reversion
    change_log = ChangeLog.create(
        "DELETE" if original_change_log.change_type == "CREATE" else "CREATE",
        user,
        original_change_log.musicc_revision,
    )

    if original_change_log.change_type == "DELETE":
        # Undelete deleted files
        original_change_log.undelete_all()
        for musicc_change in ChangeMusiccMapping.active_objects.filter(
            change_log=original_change_log
        ):
            ChangeMusiccMapping.create(change_log=change_log, musicc=musicc_change.record)

        for open_drive_change in ChangeOpenDriveMapping.active_objects.filter(
            change_log=original_change_log
        ):
            ChangeOpenDriveMapping.create(
                change_log=change_log,
                open_drive=open_drive_change.record,
                musicc=open_drive_change.musicc,
            )

        for open_scenario_change in ChangeOpenScenarioMapping.active_objects.filter(
            change_log=original_change_log
        ):
            ChangeOpenScenarioMapping.create(
                change_log=change_log,
                open_scenario=open_scenario_change.record,
                musicc=open_scenario_change.musicc,
            )

        for catalog_change in ChangeCatalogMapping.active_objects.filter(
            change_log=original_change_log
        ):
            ChangeCatalogMapping.create(
                change_log=change_log,
                catalog=catalog_change.record,
                musicc=catalog_change.musicc,
            )
        change_log.create_approval_request(request.user)

    if original_change_log.change_type == "CREATE":
        # Delete created files
        perform_logged_deletion([
            change.record
            for change in original_change_log.changemusiccmapping_set.all()
        ], change_log)

    original_change_log.reverted_by = change_log
    original_change_log.save()
    

    return HttpResponse("Change reverted successfully")
