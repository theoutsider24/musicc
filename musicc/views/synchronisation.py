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
import inspect
import os
import requests
from zipfile import ZipFile
from django.conf import settings
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers, signing
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    HttpResponseServerError,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from musicc.utils.tools import create_zip_file_stream_response
import shutil
import re
from musicc.models.BaseModel import SynchronisableModel
from musicc.models.RegisteredSystem import RegisteredSystem
from musicc.models.System import System
from django.views.decorators.csrf import csrf_exempt
from django.db.models.fields.files import FileField
from django.conf import settings
import json
from datetime import datetime
from zipfile import ZipFile, ZIP_STORED
import traceback
import tempfile

## Send a synchronisation token to the master system to request a sync file and apply the resulting synchronisation
#  @param request Type: GET<br>
#                 parameter: token - The token to authenticate the system
#  @return A HTTP response with a message indicating the operation's success
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
@user_passes_test(lambda u: u.is_superuser)
def synchronise(request):
    token = request.GET.get("token")
    response = requests.post(
        settings.MASTER_HOST + "/generate_synchronisation",
        data={
            "token": token,
            "instance_id": System.get_system_settings().system_id,
            "existing_ids": get_existing_ids(),
        },
    )
    if response.status_code == requests.codes.ok:
        response_json = {}
        download_dump_name = re.findall(
            "filename=(.+)", response.headers["Content-Disposition"]
        )[0][1:-1]
        with open(download_dump_name, "wb+") as file:
            file.write(response.content)
        # Extract all files and deserialise new records
        with ZipFile(download_dump_name, "r") as zip_file:
            with zip_file.open("new_records.json") as new_records_file:
                response_json["new_records"] = new_records_file.read()
            with zip_file.open("deleted_records.json") as deleted_records_file:
                response_json["deleted_records"] = json.load(deleted_records_file)

            new_object_count = deserialize_all_tables(
                response_json["new_records"], request.user
            )
            zip_file.extractall(settings.MEDIA_ROOT)

        deleted_records = response_json["deleted_records"]
        return HttpResponse(
            "Sync complete. {0} objects synchronised. {1} local records no longer exist in the master".format(
                new_object_count, len(deleted_records)
            )
        )
    else:
        return HttpResponseBadRequest(response.text)

## Produces a file containing the required data to synchronise the specified system
#  @param request Type: POST<br>
#                 parameter: token - The token to authenticate the system<br>
#                 parameter: existing_ids - A list of all UUIDs in the requesting system<br>
#                 parameter: instance_id - The instance id of the requesting system
#  @return A FileResponse with the synchronisation file
@csrf_exempt
def generate_synchronisation(request):
    token = request.POST.get("token")
    existing_ids = request.POST.getlist("existing_ids")
    request_instance_id = request.POST.get("instance_id")
    try:
        # Decrypt the sunchronisation token
        instance_id, last_sync = signing.loads(token, max_age=3600)
        system = RegisteredSystem.active_objects.get(instance_id=instance_id)
        # The last_sync that's in the db must match the one in the token
        # This ensures that no syncs have taken place since the token was issued
        if last_sync != system.last_sync.isoformat():
            return HttpResponseBadRequest(
                "A synchronisation has been performed since this token was issued. Please generate a new token"
            )
        # The provided system id must match that quoted in the request
        elif instance_id != request_instance_id:
            return HttpResponseBadRequest(
                "The synchronisation token does not match the provided instance id"
            )
        else:
            try:
                # Create the requested sync file
                dump_file = SyncDump(instance_id=instance_id, existing_ids=existing_ids)

                # Copy the created zip to a temporary file
                temp_file = tempfile.SpooledTemporaryFile(
                    max_size=1, dir=settings.DOWNLOAD_DIR
                )
                with open(dump_file.filename, "rb") as current:
                    shutil.copyfileobj(fsrc=current, fdst=temp_file)
                temp_file.seek(0)
                # Creates the response from the temporary zipped file
                response = create_zip_file_stream_response(
                    temp_file, os.path.basename(dump_file.filename)
                )
            except:
                traceback.print_exc()
                response = HttpResponseServerError("Error in creating the response")
            finally:
                # Delete the non-temporary file
                try:
                    os.remove(dump_file.filename)
                except:
                    pass
            return response

    except signing.SignatureExpired:
        return HttpResponseBadRequest("The synchronisation token is out of date")
    except signing.BadSignature:
        return HttpResponseBadRequest("The synchronisation token is invalid")
    except Exception:
        return HttpResponseBadRequest("An unknown exception has occurred")

## Generate a sync token for a specific system
#  @param request Type: GET<br>
#                 parameter: id - The ID of the system to sync
#  @return A HTTP response with the issued token
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def generate_synchronisation_token(request):
    instance_id = request.GET.get("id")
    # Ensure that the specified simulator is registered, active and belongs to the requesting user
    system = get_object_or_404(
        RegisteredSystem.active_objects,
        instance_id=instance_id,
        updated_by_user=request.user,
    )
    # Create a token containing the instance_id and las sync time
    one_time_token = signing.dumps((instance_id, system.last_sync.isoformat()))
    return HttpResponse(one_time_token)

## Get a list of every object which needs to be serialised as well as those files which need to be transferred
#  @param kwargs Arguments which can used to construct a Q object to exclude records
#  @return A list of objects
#  @return A list of file objects
def get_all_serialisable_objects(**kwargs):
    all_objects = []
    file_objects = []
    # Iterate through each applicable model
    for model in get_serialisable_models():
        # Get all objects using should_be_synchronised and the provided kwargs to exclude objects
        new_objects = [
            new_object
            for new_object in model.active_objects.all().exclude(Q(**kwargs))
            if new_object.should_be_synchronised()
        ]
        all_objects.extend(new_objects)
        # Get any FileField contained in the current model
        file_fields = [
            field.name for field in model._meta.fields if isinstance(field, FileField)
        ]
        # If a field was found, get the value of that field for each discovered object and store it
        if file_fields:
            for obj in new_objects:
                for field in file_fields:
                    file_field = getattr(obj, field)
                    file_objects.append(file_field)

    return all_objects, file_objects

## Given a list of ids, determine which of them are no longer active
#  @param existing_ids A list of UUIDs
#  @return A list of those ids which are no longer active
def get_deleted_ids(existing_ids):
    inactive_records = []
    for model in get_serialisable_models():
        inactive_records.extend(model.objects.filter(active=False, id__in=existing_ids))
    inactive_ids = [record.id for record in inactive_records]
    return inactive_ids

## Get a list of every non-abstract Model which inherits SynchronisableModel
#  @return A list of models ordered based on foreign key inter-dependencies
def get_serialisable_models():
    # Define a function which can get recursively get all relevant subclasses
    def inheritors(klass):
        subclasses = set()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                # If we haven't already recorded this subclass and it's not an abstract class
                if child not in subclasses and not inspect.isabstract(child):
                    # If it's not an abstract model
                    if not child._meta.abstract:
                        subclasses.add(child)
                    # Explore the subclasses of this model
                    work.append(child)
        return subclasses

    return sort_foreign_key_relations(inheritors(SynchronisableModel))

## Deserialise a json serialisation of objects
#  @param data The JSON-serialised data
#  @param user The user to whom the created scenarios will be attributed
#  @return The number of new objects created
def deserialize_all_tables(data, user):
    object_generator = serializers.deserialize("json", data)
    new_object_count = 0
    for obj in object_generator:
        obj.object.updated_by_user = user
        obj.save()
        new_object_count = new_object_count + 1
    return new_object_count

## Get a list of every serialisable object's UUID
#  @return A list of UUIDs
def get_existing_ids():
    all_objects, _ = get_all_serialisable_objects()
    all_ids = [object.id.hex for object in all_objects]
    return all_ids

## Reorder the list of models to ensure any model which depends on another is below its dependency
#  @param all_models The list of models
#  @return The sorted list
def sort_foreign_key_relations(all_models):
    all_models = list(all_models)
    sorted_models = []

    while all_models:
        for model in all_models:
            foreign_models = []
            for field in model._meta.fields:
                if field.get_internal_type() == "ForeignKey":
                    foreign_models.append(field.remote_field.model)
            can_write = True
            for foreign_model in foreign_models:
                if foreign_model in all_models:
                    can_write = False
            if can_write:
                sorted_models.append(all_models.pop(all_models.index(model)))
    return sorted_models


class SyncDump(ZipFile):
    def __init__(self, instance_id, existing_ids=[]):
        super(SyncDump, self).__init__(
            os.path.join(
                settings.DOWNLOAD_DIR,
                "{}-{}.dump".format(
                    instance_id, datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                ),
            ),
            mode="w",
            compression=ZIP_STORED,
        )
        self.existing_ids = existing_ids
        self.serialize_all_tables()
        self.close()

    ## Serialize all relevant files and write the resulting serialisation to a file
    ## Write the ids of deleted records to another file
    ## Write all relevant files to the zip
    def serialize_all_tables(self):
        all_objects, file_objects = get_all_serialisable_objects(
            id__in=self.existing_ids
        )
        data = serializers.serialize("json", all_objects)

        self.writestr("new_records.json", data)

        deleted_ids = get_deleted_ids(self.existing_ids)
        deleted_ids_json = json.dumps(deleted_ids)
        self.writestr("deleted_records.json", deleted_ids_json)

        for file in file_objects:
            filename = file.name
            full_path = os.path.join(settings.MEDIA_ROOT, filename)
            self.write(full_path, filename)

