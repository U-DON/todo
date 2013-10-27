from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    timezone = models.CharField(max_length=10)

    def __unicode__(self):
        return self.user.username
