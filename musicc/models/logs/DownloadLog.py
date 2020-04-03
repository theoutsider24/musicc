from django.db import models
from musicc.models.BaseModel import BaseModel
from musicc.models.QueryCache import QueryCache
import pickle


class DownloadLog(BaseModel):
    seed = models.BinaryField()
    query = models.ForeignKey("QueryCache", on_delete=models.CASCADE)
    download_size = models.PositiveIntegerField()
    download_type = models.CharField(
        choices=(("Native", "NATIVE"), ("Non-native", "NON-NATIVE")), max_length=16
    )
    concrete_per_logical = models.PositiveIntegerField()

    @classmethod
    def create(cls, numpy_state, query_id, download_size, user, native, concrete_per_logical):
        log = cls(
            seed=pickle.dumps(numpy_state),
            query=QueryCache.objects.get(pk=query_id),
            download_size=download_size,
            updated_by_user=user,
            download_type="NATIVE" if native else "NON_NATIVE",
            concrete_per_logical=concrete_per_logical
        )
        log.save()
        return log

    def to_dict(self):
        return {
            "id": self.id,
            "query": '"{0}"'.format(self.query.query_string),
            "query_id": self.query.id,
            "musicc_revision": self.query.musicc_revision.revision,
            "type": self.download_type,
            "user": self.updated_by_user.username,
            "date": self.updated_date_time,
            "concrete_per_logical" : self.concrete_per_logical
        }
        
    def __str__(self):
        return self.download_type + " - " + self.updated_date_time.strftime("%m/%d/%Y, %H:%M:%S") + " - " + self.updated_by_user.username
