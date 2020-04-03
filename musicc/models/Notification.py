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
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import models
from musicc.models.Tag import Tag
from django.conf import settings

from musicc.models.BaseModel import BaseModel

User = get_user_model()

notification_categories = (
    ("revision_activation", "Revision Activation"),
    ("scenario_added", "New Scenario Added"),
    ("comment_on_favourite", "Comment on Favourited Scenario"),
    ("favourite_broken", "Favourited Scenario Reported as Broken"),
    ("submission_approved", "Submission Approved"),
    ("submission_denied", "Submission Denied"),
    ("favourite_updated", "Favourited Scenario Updated"),
    ("favourite_deleted", "Favourited Scenario Deleted"),
    ("new_approval_request", "A new approval request has been submitted"),
    ("software_version_upgrade", "A new version of the MUSICC system has been deployed"),
    ("custom", "A custom notification")
)


class Notification(BaseModel):
    message = models.CharField(max_length=256)
    seen = models.BooleanField(default=False)
    category = models.CharField(choices=notification_categories, max_length=64)

    def notify_revision_activation(revision):
        return Notification.create_notifications(
            "revision_activation",
            "Revision {0} of MUSICC has been activated".format(revision.revision),
        )

    def notify_scenario_added(musicc_scenario):
        return Notification.create_notifications(
            "scenario_added",
            "A new scenario '<a href = '#{0}'>{1}</a>' has been added".format(musicc_scenario.get_human_readable_id(), musicc_scenario.label),
        )

    def notify_comment_on_favourite(comment):        
        favourited_users = Tag.get_users_who_favourited(comment.musicc).exclude(id = comment.updated_by_user.id)
        if comment.scenario_broken:
            # If it's a "broken" comment, send "broken" notifications to subscribers and "comment" notifications to others
            return (Notification.create_notifications(
                "comment_on_favourite",
                "{0} has left a comment on your favourited scenario '<a href = '#{1}'>{2}</a>'".format(
                    comment.updated_by_user.get_full_name(), comment.musicc.get_human_readable_id(), comment.musicc.label
                ),
                favourited_users.filter(
                    notificationexclusions__category__contains="favourite_broken"
                )
            ) + Notification.create_notifications(
                "favourite_broken",
                "{0} has reported that your favourited scenario '<a href = '#{1}'>{2}</a>' may be broken".format(
                    comment.updated_by_user.get_full_name(), comment.musicc.get_human_readable_id(), comment.musicc.label
                ),
                favourited_users
            ))
        else:
            return Notification.create_notifications(
                "comment_on_favourite",
                "{0} has left a comment on your favourited scenario '<a href = '#{1}'>{2}</a>'".format(
                    comment.updated_by_user.get_full_name(), comment.musicc.get_human_readable_id(), comment.musicc.label
                ),
                favourited_users
            )

    def notify_submission_approved(approval_request):
        return Notification.create_notifications(
            "submission_approved",
            "You submission of change #{0} has been approved".format(
                approval_request.change.id
            ),
            User.objects.filter(id=approval_request.change.updated_by_user.id)
        )

    def notify_submission_denied(approval_request):
        return Notification.create_notifications(
            "submission_denied",
            "You submission of change #{0} has been denied".format(
                approval_request.change.id
            ),
            User.objects.filter(id=approval_request.change.updated_by_user.id)
        )

    def notify_favourite_updated(musicc_scenario):
        favourited_users = Tag.get_users_who_favourited(musicc_scenario)
        return Notification.create_notifications(
            "favourite_updated",
            "Your favourited scenario '<a href = '#{0}'>{1}</a>' has been updated".format(
                musicc_scenario.get_human_readable_id(), musicc_scenario.label
            ),
            favourited_users
        )

    def notify_favourite_deleted(musicc_scenario):
        favourited_users = Tag.get_users_who_favourited(musicc_scenario)
        return Notification.create_notifications(
            "favourite_deleted",
            "Your favourited scenario '{0}' has been deleted".format(
                musicc_scenario.label
            ),
            favourited_users
        )

    def notify_new_approval_request(approval_request):
        return Notification.create_notifications(
            "new_approval_request",
            "A new approval request for change #{0} has been submitted".format(
                approval_request.change.id
            ),
            User.objects.exclude(id=approval_request.updated_by_user.id).filter(groups__name__contains = "curator")
        )

    def notify_software_version_upgrade():
        return Notification.create_notifications(
            "software_version_upgrade",
            "The MUSICC system has been updated to version {0}<br>See the <a href='/release_notes'>release notes</a> for details".format(
                settings.MUSICC_VERSION
            )
        )

    def notify_custom_notification(message):
        return Notification.create_notifications(
            "custom",
            message
        )

    def get_subsribed_users(category, user_subset = None):
        if user_subset == None:
            user_subset = User.objects.all()
        return user_subset.filter(is_active=True).exclude(
            notificationexclusions__category__contains=category
        )

    @classmethod
    def create_notifications(cls, category, message, user_subset = None):
        return cls.objects.bulk_create(
            [
                cls(updated_by_user=user, category=category, message=message)
                for user in cls.get_subsribed_users(category, user_subset)
            ]
        )

    def count_unseen_notifications(user):
        return Notification.get_user_notifications(user).filter(seen=False).count()

    def get_user_notifications(user, page=None):
        notifications_per_page = 5
        notifications = user.notification_set.filter(active=True).order_by("-updated_date_time")
        if page:
            paginator = Paginator(notifications, notifications_per_page)
            notifications = paginator.get_page(page)
        return notifications


class NotificationExclusions(BaseModel):
    category = models.CharField(choices=notification_categories, max_length=64)

    @classmethod
    def create(cls, user, category):
        cls(updated_by_user=user, category=category).save()
