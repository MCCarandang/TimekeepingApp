from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    # Additional fields can be added here
    pass

class RFIDTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag_id = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)