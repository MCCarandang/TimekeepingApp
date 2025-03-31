from django.db import models

# This model is where the attendance records will be stored.
class Attendance(models.Model):
    rfid_tag = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10)

#This method determines what gets displayed, when you query the database and print an Attendance.
    def __str__(self):
        return f"{self.rfid_tag} - {self.status} at {self.timestamp}"