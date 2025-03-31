from django.db import models

# This model is to store user information and their RFID tags.
class User(models.Model):
    name = models.CharField(max_length=100)
    rfid_tag = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name