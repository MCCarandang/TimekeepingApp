from django.db import models

# User model to store user information and their RFID tags
class User(models.Model):
    name = models.CharField(max_length=100)
    rfid_tag = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Attendance model to store attendance records
class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)    # Link to User model
    timestamp = models.DateTimeField(auto_now_add=True)     # Automatically set the timestamp when created
    status = models.CharField(max_length=10)    # Status can be 'IN' or 'OUT'

#This method determines what gets displayed, when you query the database and print an Attendance.
    def __str__(self):
        return f"{self.user.name} - {self.status} at {self.timestamp}"