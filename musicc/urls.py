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
"""musicc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView
from musicc.views.documentation import documentation
from musicc.views.signup import terms_and_conditions, signup, privacy_policy, update_terms_and_conditions
from musicc.views.search import (
    search,
    query,
    release_notes,
    detail,
    diff_version,
    diff_change_logs,
    profile,
)
from musicc.views import (
    curation,
    metadata,
    download,
    delete,
    feedback,
    notifications,
    system,
    synchronisation,
)
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    # GET
    path("search", search, name="search"),
    path("search/detail", detail, name="detail"),
    path("search/detail/diff", diff_version, name="diff_version"),
    path("search/detail/diff/change", diff_change_logs, name="diff_change_logs"),
    path("download", download.download_query_results, name="download_query_results"),
    path(
        "download/individual",
        download.download_individual_musicc,
        name="download_individual",
    ),
    path("search/detail/comment", feedback.add_comment, name="comment"),
    path(
        "search/detail/comment/delete", feedback.delete_comment, name="delete_comment"
    ),
    path(
        "search/detail/comment/undelete",
        feedback.undelete_comment,
        name="undelete_comment",
    ),
    path(
        "search/detail/comment/disable",
        feedback.disable_comments,
        name="disable_comments",
    ),
    path("search/detail/comment/lock", feedback.lock_comments, name="lock_comments"),
    path(
        "search/detail/comment/enable", feedback.enable_comments, name="enable_comments"
    ),
    path(
        "search/detail/comment/unlock", feedback.unlock_comments, name="unlock_comments"
    ),
    path("search/detail/tag/add", feedback.add_tag, name="add_tag"),
    path("search/detail/tag/remove", feedback.remove_tag, name="remove_tag"),
    path("notifications", notifications.get_notifications, name="get_notifications"),
    path("profile", profile, name="profile"),
    path("dump/musicc", download.dump_records, name="dump_musicc"),
    path("dump/schema", download.dump_schema, name="dump_schema"),
    path("query", query, name="query"),
    path("", RedirectView.as_view(url="/search")),
    path("curation", curation.get_curation_html, name="upload"),
    path("curation/change_log", curation.get_change_log, name="change_log"),
    path("curation/approval_queue", curation.get_approval_queue, name="approval_queue"),
    path(
        "curation/submissions_queue",
        curation.get_submissions_queue,
        name="submissions_queue",
    ),
    path("curation/approve", curation.approve_change, name="approve"),
    path("curation/reject", curation.reject_change, name="reject"),
    path(
        "curation/change_log/summary",
        curation.get_change_summary,
        name="change_summary",
    ),
    path("curation/download_change", download.download_changed_scenarios, name="download_change"),
    path("curation/download_log", curation.get_download_log, name="download_log"),
    path(
        "curation/download_log/summary",
        curation.get_download_summary,
        name="download_summary",
    ),
    #
    path(
        "curation/editable_musicc", curation.get_editable_musicc, name="editable_musicc"
    ),
    path(
        "curation/editable_musicc/validate",
        curation.validate_musicc_from_editor,
        name="validate_musicc",
    ),
    path(
        "curation/editable_musicc/submit",
        curation.apply_musicc_edit,
        name="submit_musicc",
    ),
    path("delete", delete.delete_musicc, name="delete"),
    path("revert", delete.revert_change, name="revert"),
    path("get_revision_info", curation.get_revision_info, name="get_revision_info"),
    path("get_metadata_fields", metadata.get_metadata, name="get_metadata"),
    path("activate_revision", curation.activate_revision, name="activate_revision"),
    path("upload_revisions", curation.upload_revisions, name="upload_revisions"),
    path("upload_zip", curation.upload_zip, name="upload_zip"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("terms_and_conditions", terms_and_conditions, name="terms_and_conditions"),
    path("privacy_policy", privacy_policy, name="privacy_policy"),
    path("signup/update_terms_and_conditions", update_terms_and_conditions, name="update_terms_and_conditions"),
    path("signup/", signup, name="signup"),
    path("admin/", admin.site.urls),
    path("system", system.get_system_html, name="system"),
    path("system/deactivate", system.deactivate_system, name="deactivate_system"),
    path("system/reactivate", system.reactivate_system, name="reactivate_system"),
    path("system/registered_systems", system.get_registered_systems, name="registered_systems"),
    path("system/my_registered_systems", system.get_my_registered_systems, name="my_registered_systems"),
    path(
        "generate_synchronisation",
        synchronisation.generate_synchronisation,
        name="generate_synchronisation",
    ),
    path("synchronisation_token", synchronisation.generate_synchronisation_token, name="synchronisation_token"),
    path(
        "register_system", system.accept_instance_registration, name="register_system"
    ),
    path(
        "register_system_with_master",
        system.register_system_with_master,
        name="register_system_with_master",
    ),
    path(
        "registration_token", system.get_registration_token, name="registration_token"
    ),
    path("synchronise", synchronisation.synchronise, name="synchronise"),
    path("release_notes", release_notes),
    re_path(r'^docs/(?P<path>.*)$', documentation, name="mkdocs"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

