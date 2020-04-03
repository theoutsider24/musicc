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
from musicc.models.revisions.MusiccRevision import MusiccRevision
from musicc.models.revisions.BaseRevision import BaseRevision
from musicc.models.MusiccScenario import MusiccScenario
from musicc.models.Tag import Tag
from django.http import JsonResponse
from musicc.utils import xsd_parser
from django.http import Http404
import json
from django.db import models
from musicc.views.decorators import user_agreed_t_and_c_check
from django.contrib.auth.decorators import login_required, user_passes_test
import zipfile
import logging
import io
from musicc.utils.xml_functions import find_base_xsd_file

logger = logging.getLogger("musicc")

## Get a JSON schema representation of the target MUSICC revision
#  @param request Type: GET<br>
#                 parameter: revision[optional] - [default:The latest revision] The target revision
#  @return A HTTP response with a JSON schema
@login_required
@user_passes_test(user_agreed_t_and_c_check, login_url='/signup/update_terms_and_conditions')
def get_metadata(request):
    revision = request.GET.get("revision", None)
    if revision != None:
        try:
            musicc_revision = MusiccRevision.active_objects.get(revision=revision)
        except MusiccRevision.DoesNotExist:
            logger.error(
                "[User:{0}] No Musicc revision found for metadata for revision {1}".format(
                    request.user, revision
                )
            )
            raise Http404("Revision doesn't exist")
    else:
        try:
            musicc_revision = MusiccRevision.latest_revision()
        except MusiccRevision.DoesNotExist:
            logger.error(
                "[User:{0}] No Musicc revision found for metadata".format(request.user)
            )
            raise Http404("No revisions available")

    metadata_json_schema = extract_musicc_json_schema(musicc_revision)

    # If there are GlobalTags in this revision, we need to merge with them with user tags
    if "GlobalTags" in metadata_json_schema["properties"]:
        metadata_json_schema["properties"]["GlobalTags"]["properties"]["Tag"] = metadata_json_schema["properties"]["GlobalTags"]["properties"].pop("GlobalTag")
        metadata_json_schema["properties"]["Tags"] = metadata_json_schema["properties"].pop("GlobalTags")

        # For each scenario, extract global tags if they exist
        deep_tag_list = [m.metadata["GlobalTags"]["GlobalTag"] for m in MusiccScenario.get_latest_scenarios(revision=musicc_revision) if "GlobalTags" in m.metadata and "GlobalTag" in m.metadata["GlobalTags"]]
        # The list is nested, flatten the child lists
        flat_tag_list = [item for sublist in deep_tag_list for item in sublist]
        # Remove duplicates
        unique_tags = list(set(flat_tag_list))
        # Append user tags
        unique_tags.extend(list(set([tag.name for tag in Tag.active_objects.filter(updated_by_user = request.user, musicc__revision = musicc_revision)])))

        # Add all tags as an enumerated list of values for the Tag field
        metadata_json_schema["properties"]["Tags"]["properties"]["Tag"]["properties"]["value"]["enum"] = unique_tags

    # Revision searching is unneccessary so remove this field
    del metadata_json_schema["properties"]["revision"]

    return JsonResponse(metadata_json_schema)

## Return a JSON schema representation of an XSD
#  @param revision_xsd This may be either BaseRevision object or a string-representation of an XSD file
#  @return A JSON schema-style dict
def extract_musicc_json_schema(revision_xsd):
    if isinstance(revision_xsd, BaseRevision):
        # If the XSDs are zipped, there are multiple linked files
        # Identify the base file and read it
        if zipfile.is_zipfile(io.BytesIO(bytes(revision_xsd.revision_xsd))):
            zip_file = zipfile.ZipFile(io.BytesIO(bytes(revision_xsd.revision_xsd)))
            base_xsd_file = find_base_xsd_file(zip_file, "MUSICCScenario")
            with zip_file.open(base_xsd_file) as xsd_file:
                xsd = xsd_file.read()
        else:
            xsd = revision_xsd.revision_xsd
        revision_xsd = bytes(xsd)

    # Covert the XSD to JSON schema
    parsed_xsd = xsd_parser.XSDParser(revision_xsd)
    full_json_schema = json.loads(parsed_xsd.json_schema())

    # Re-construct the properties to expose FileHeader properties at the same level as standard properties
    metadata_json_schema = full_json_schema["properties"]["MUSICCScenario"][
        "properties"
    ]["FileHeader"]

    metadata_json_schema["properties"]["MUSICC_ID"] = {"type": "string"}
    metadata_json_schema["properties"]["OpenScenario_ID"] = {"type": "string"}
    metadata_json_schema["properties"]["OpenDrive_ID"] = {"type": "string"}

    metadata_json_schema["properties"].update(
        full_json_schema["properties"]["MUSICCScenario"]["properties"]["Metadata"][
            "properties"
        ]
    )

    return metadata_json_schema
