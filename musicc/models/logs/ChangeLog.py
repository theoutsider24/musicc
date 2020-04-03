from django.db import models
from musicc.models.BaseModel import BaseModel
from musicc.models.ApprovalRequest import ApprovalRequest


class ChangeLog(BaseModel):
    filename = models.CharField(max_length=500, blank=True, null=True)
    file_hash = models.CharField(max_length=500, blank=True, null=True)
    change_type = models.CharField(
        choices=(("DELETE", "DELETE"), ("CREATE", "CREATE")), max_length=16
    )
    reverted_by = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    musicc_revision = models.ForeignKey(
        "MusiccRevision", on_delete=models.CASCADE, to_field="revision"
    )

    @classmethod
    def create(cls, change_type, user, musicc_revision, filename = None, file_hash = None):

        change_log = cls(
            change_type=change_type,
            filename=filename,
            updated_by_user=user,
            file_hash=file_hash,
            musicc_revision=musicc_revision
        )
        change_log.save()

        return change_log

    def __str__(self):
        return self.change_type + " - " + self.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S") + " - " + self.updated_by_user.username

    def undelete_all(self):
        for change_model in [
            ChangeMusiccMapping,
            ChangeOpenDriveMapping,
            ChangeOpenScenarioMapping,
            ChangeCatalogMapping,
        ]:
            for change in change_model.active_objects.filter(
                change_log=self
            ):
                change.record.undelete()

    def create_approval_request(self, user):
        if not self.is_empty():
            ApprovalRequest.create(user, self)

    def is_empty(self):
        for change_model in [
            ChangeMusiccMapping,
            ChangeOpenDriveMapping,
            ChangeOpenScenarioMapping,
            ChangeCatalogMapping,
        ]:
            for _ in change_model.active_objects.filter(
                change_log=self
            ):
                return False
        return True

class BaseChangeMapping(BaseModel):
    change_log = models.ForeignKey("ChangeLog", on_delete=models.CASCADE)
    filename = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        abstract = True

class ChangeMusiccMapping(BaseChangeMapping):
    record = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE, blank=True, null=True, db_column="musicc_id")

    @classmethod
    def create(cls, change_log, filename=None, musicc=None):
        change_musicc_mapping = cls(
            change_log=change_log,
            record=musicc,
            filename=filename,
        )

        change_musicc_mapping.save()

        return change_musicc_mapping
   

class ChangeOpenScenarioMapping(BaseChangeMapping):
    record = models.ForeignKey("OpenScenario", on_delete=models.CASCADE, blank=True, null=True, db_column="open_scenario_id")
    musicc = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE, blank=True, null=True)

    @classmethod
    def create(cls, change_log, filename=None, open_scenario=None, musicc=None):
        open_scenario_mapping = cls(
            change_log=change_log,
            record=open_scenario,
            filename=filename,
            musicc=musicc,
        )

        open_scenario_mapping.save()

        return open_scenario_mapping


class ChangeOpenDriveMapping(BaseChangeMapping):
    record = models.ForeignKey("OpenDrive", on_delete=models.CASCADE, blank=True, null=True, db_column="open_drive_id")
    musicc = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE, blank=True, null=True)


    @classmethod
    def create(cls, change_log, filename=None, open_drive=None, musicc=None):
        open_drive_mapping = cls(
            change_log=change_log,
            record=open_drive,
            filename=filename,
            musicc=musicc,
        )

        open_drive_mapping.save()

        return open_drive_mapping

class ChangeCatalogMapping(BaseChangeMapping):
    record = models.ForeignKey("Catalog", on_delete=models.CASCADE, blank=True, null=True, db_column="catalog_id")
    musicc = models.ForeignKey("MusiccScenario", on_delete=models.CASCADE, blank=True, null=True) 
    
    @classmethod
    def create(cls, change_log, filename=None, catalog=None, musicc=None):
        catalog_mapping = cls(
            change_log=change_log,
            record=catalog,
            filename=filename,
        )

        catalog_mapping.save()

        return catalog_mapping
   