from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    photo_url = models.URLField(null=True, default=None)

    def __str__(self):
        return self.username