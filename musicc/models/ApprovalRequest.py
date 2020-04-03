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
from django.db import models
from rolepermissions.checkers import has_role

from musicc.models.BaseModel import BaseModel
from musicc.models.Notification import Notification

User = get_user_model()

class ApprovalRequest(BaseModel):
    submitted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, to_field="username", null=True, blank=True, related_name="submitter"
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, to_field="username", null=True, blank=True, related_name="reviewer"
    )
    change = models.ForeignKey("ChangeLog", on_delete=models.CASCADE)
    status = models.CharField(
        choices=(("APPROVED", "APPROVED"), ("DENIED", "DENIED"), ("PENDING", "PENDING"), ("CANCELLED", "CANCELLED")), max_length=16
    )

    @classmethod
    def create(cls, submitting_user, change):
        request = cls(
            updated_by_user = submitting_user,
            submitted_by = submitting_user,
            change = change,
            status = "PENDING"
        )

        request.save()
        Notification.notify_new_approval_request(request)

        return request

    def __str__(self):
        return self.status + " - " + self.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S") + " - " + self.updated_by_user.username

    def approve(self, user):
        if user != self.submitted_by:
            if has_role(self.submitted_by, "curator"):
                if self.change.change_type == "CREATE":
                    self.change.undelete_all()
                    for musicc in [m.record for m in self.change.changemusiccmapping_set.all()]:
                        if not musicc.version:
                            musicc.assign_new_version_number() 
                    Notification.notify_submission_approved(self)
            else:
                request = ApprovalRequest(
                    updated_by_user = user,
                    submitted_by = user,
                    change = self.change,
                    status = "PENDING"
                )
                request.save()
            
            self.status="APPROVED"
            self.reviewed_by=user
            self.save()   
        else:
            #user tried to approve own request
            raise Exception("A user cannot approve their own request")

    def reject(self, user):
        self.status="DENIED"
        self.reviewed_by=user
        Notification.notify_submission_denied(self)
        self.save()

    def cancel(self, user):
        self.status="CANCELLED"
        self.save()
