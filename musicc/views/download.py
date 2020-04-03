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
import os
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

User = get_user_model()

from django.shortcuts import get_object_or_404
from musicc.models.QueryCache import QueryCache
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.MusiccScenario import MusiccScenario
from musicc.utils.queries import QueryParser
from musicc.models.logs.DownloadLog import DownloadLog
from musicc.models.logs.ChangeLog import ChangeLog
import pickle
from django.conf import settings
import shutil
from musicc.utils.ExportZipCreator import ExportZipCreator
from django.http import HttpResponse, Http404, HttpResponseServerError
from datetime import datetime
from musicc.utils.tools import create_zip_file_stream_response, delete_folder_if_exists
import tempfile
import logging
from rolepermissions.decorators import has_role_decorator
from django.contrib.auth.decorators import login_required

logger = logging.getLogger("musicc")

## Download the scenarios from a particular query
#  @param request Type: GET<br>
#                 parameter: query_id - The id of the query<br>
#                 parameter: previous_download_id[optional] - The id of a previous download whose randomisations we wish to repeat<br>
#                 parameter: native[optional] - [default:"true"] Whether we want native (non-randomised incl. MUSICC file) or non-native (randomised without MUSICC file)<br>
#                 parameter: concrete_per_logical[optional] - [default:1] How many conrete scenarios to generate for each logical one<br>
#                 parameter: exclude_resources[optional] - [default:"false"] Whether or not to exclude resources from the download<br>
#                 parameter: exclude_images[optional] - [default:"false"] Whether or not to exclude images from the download
#  @return A FileResponse with the download
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def download_query_results(request):
    user = User.objects.get(username=request.user)

    query_id = request.GET.get("query_id")
    previous_download_id = request.GET.get("previous_download_id", None)
    native = request.GET.get("native", "true").lower() == "true"
    concrete_per_logical = request.GET.get("concrete_per_logical", "1")
    exclude_resources = request.GET.get("exclude_resources", "false").lower() == "true"
    exclude_images = request.GET.get("exclude_images", "false").lower() == "true"
    concrete_per_logical = (
        int(concrete_per_logical) if concrete_per_logical.isnumeric() else 1
    )
    if native:
        concrete_per_logical = 1
    # Only allow between 1 and 100 randomisations
    concrete_per_logical = max(1, min(concrete_per_logical, 100))

    if not QueryCache.objects.filter(pk=query_id).exists():
        logger.info(
            "[User:{0}] Query ID doesn't exist: {1}".format(request.user, query_id)
        )
        return HttpResponseServerError("Query ID doesn't exist")

    target_numpy_seed = None
    if (
        previous_download_id is not None
        and DownloadLog.active_objects.filter(
            pk=int(previous_download_id), query_id=query_id
        ).exists()
    ):
        previous_download = DownloadLog.active_objects.get(pk=int(previous_download_id))
        target_numpy_seed = pickle.loads(previous_download.seed)
        concrete_per_logical = previous_download.concrete_per_logical
    elif previous_download_id is not None:
        return HttpResponseServerError("No matching previous download exists")

    query = QueryCache.objects.get(pk=query_id)
    return get_download_response(
        query, user, target_numpy_seed, native, concrete_per_logical, exclude_resources=exclude_resources, exclude_images=exclude_images
    )

## Download a specific MUSICC scenario
#  @param request Type: GET<br>
#                 parameter: id - The UUID of the MUSICC scenario
#  @return A FileResponse with the specified scenario
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def download_individual_musicc(request):
    id = request.GET.get("id")
    musicc = MusiccScenario.active_objects.get(pk=id)
    musicc_query_set = MusiccScenario.active_objects.filter(pk=id)
    native = request.GET.get("native", "true").lower() == "true"

    query = QueryCache.create(
        "Single download - {0}".format(musicc.get_human_readable_id()),
        musicc_query_set,
        musicc.revision.revision,
        request.user,
    )
    # Immediately delete the QueryCache entry - It's not worth keeping
    query.delete()
    return get_download_response(query, request.user, native=native)

## Download all of the most recent active MUSICC versions
#  @param request Type: GET<br>
#                 parameter: revision[optional] - [default: The latest revision] The MUSICC revision for which to dump scenarios
#  @return A FileResponse with the scenarios
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def dump_records(request):
    user = User.objects.get(username=request.user)
    revision = request.GET.get("revision", MusiccRevision.latest_revision().revision)

    # Check if there's an active QueryCache we can use
    result_set = QueryCache.active_objects.filter(
        query_string__in=["", "*"], musicc_revision__revision=revision
    )
    if result_set.exists():
        query = result_set[0]
    else:
        query_string = ""
        musicc_scenario_highest_versions = MusiccScenario.get_latest_scenarios(revision)
        query_as_q_object = QueryParser(query_string).evaluate(request.user)
        query_set = musicc_scenario_highest_versions.filter(query_as_q_object)
        query = QueryCache.create(query_string, query_set, revision, request.user)
    return get_download_response(query, user)

## Download the XSDs for a given revision
#  @param request Type: GET<br>
#                 parameter: revision[optional] - [default: The latest revision] The MUSICC revision for which to dump schemas
#  @return A FileResponse with the osc, odr and MUSICC XSDs
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def dump_schema(request):
    revision = request.GET.get("revision", MusiccRevision.latest_revision().revision)
    revision = MusiccRevision.active_objects.get(revision=revision)

    file_path = revision.get_combined_zip()
    
    # Copy the created zip to a temporary file
    temp_file = tempfile.SpooledTemporaryFile(max_size=1, dir=settings.DOWNLOAD_DIR)
    with open(file_path, "rb") as current:
        shutil.copyfileobj(fsrc=current, fdst=temp_file)
    temp_file.seek(0)

    # Creates the response from the temporary zipped file
    response = create_zip_file_stream_response(temp_file, os.path.basename(file_path))
    return response

## Download the MUSICC scenarios affected by a ChangeLog 
#  @param request Type: GET<br>
#                 parameter: token - A registration token
#  @return A HTTP response with the system's new id
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@has_role_decorator("curator")
def download_changed_scenarios(request):
    change_log = get_object_or_404(ChangeLog, pk=request.GET.get("id"))
    records = [mapping.record for mapping in change_log.changemusiccmapping_set.all()]
    query = QueryCache.create(
        "Change Log {}".format(change_log.id),
        records,
        change_log.musicc_revision.revision,
        request.user,
    )
    return get_download_response(query, request.user, log=False)

## Create a requested scenario download
#  @param query A QueryCache entry to use
#  @param user The user performing the download
#  @param target_numpy_seed [Optional]A pickled numpy for reproducing randomisations
#  @param native [Optional]Default:True Whether the download is native or non-native
#  @param concrete_per_logical [Optional]Default:1 How many concrete scenarios to generate for each logical scenario
#  @param log [Optional]Default:True Whether a DownloadLog entry should be produced
#  @param exclude_resources [Optional]Default:False Whether to exclude resources from the download
#  @param exclude_images [Optional]Default:False Whether to exclude images from the download
#  @return A FileResponse with the download zip
def get_download_response(
    query, user, target_numpy_seed=None, native=True, concrete_per_logical=1, log=True, exclude_resources=False, exclude_images=False
):
    # Creates name of zipped folder to be downloaded
    target_file_name = "query_results_%s_%s.zip" % (query.id, user.id)

    # Path of download directory for the current users query
    # This supports multiple users and queries
    date_time_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    download_dir = os.path.join(
        settings.DOWNLOAD_DIR,
        "Download_%s_%s_%s" % (query.id, user.id, date_time_string),
    )

    export_folder = None
    try:
        delete_folder_if_exists(download_dir)
        os.makedirs(download_dir, exist_ok=True)

        # Creates a zip file with the appropriate folder structure for each MusiccScenario
        export_folder = ExportZipCreator(
            results=query.results,
            file_path=os.path.join(download_dir, target_file_name),
            numpy_state=target_numpy_seed,
            native=native,
            concrete_per_logical=concrete_per_logical,
            exclude_resources=exclude_resources,
            exclude_images=exclude_images
        )

        # Record the details of the download
        file_size = os.path.getsize(export_folder.file_path)
        if log:
            DownloadLog.create(
                export_folder.numpy_state,
                query.id,
                file_size,
                user,
                native,
                concrete_per_logical,
            )
        # Copy the created zip to a temporary file
        temp_file = tempfile.SpooledTemporaryFile(max_size=1, dir=settings.DOWNLOAD_DIR)
        with open(export_folder.file_path, "rb") as current:
            shutil.copyfileobj(fsrc=current, fdst=temp_file)
        temp_file.seek(0)

        # Creates the response from the temporary zipped file
        response = create_zip_file_stream_response(temp_file, target_file_name)
    except:
        logger.exception(
            "[User:{0}] Error in creating download response for id {1}".format(
                user, query.id
            )
        )
        response = HttpResponseServerError("Error in creating the response")
    finally:
        # Delete the non-temporary file and directory
        if export_folder:
            os.unlink(export_folder.file_path)
        delete_folder_if_exists(download_dir)
    return response
