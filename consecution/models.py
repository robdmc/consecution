import uuid
from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=64, unique=True)
    #uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uuid = models.UUIDField()
