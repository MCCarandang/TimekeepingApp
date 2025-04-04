from django.shortcuts import render
from django.http import JsonResponse  # To return JSON responses
from .models import Attendance, User      #imports the models.py from attendance app
from django.utils import timezone
import pytz

# Create your views here.
def scan_rfid(request):
    current_time_utc = timezone.now()

    # Convert to Philippine Time
    philippine_tz = pytz.timezone('Asia/Manila')
    current_time = current_time_utc.astimezone(philippine_tz)

    current_date = current_time.date()  # Get the date
    current_time_only = current_time.time() # Get the time
    return render(request, 'attendance/scan_rfid.html', {
        'current_date': current_date,
        'current_time': current_time_only
        })  # Gets the current date and time using Django's timezone.now(). This ensures time is stored in a timezone-aware format.

# Django view that calls check_in_out()
def record_attendance(request):
    access_message = ""
    if request.method == 'POST':
        rfid_tag = request.POST.get('rfid_tag')
        
        # Check if the RFID tag is valid
        try:
            user = User.objects.get(rfid_tag=rfid_tag)
            access_message = "Access Granted! You can clock in/out."
            
            # Check the last attendance record
            last_record = Attendance.objects.filter(rfid_tag=rfid_tag).order_by('timestamp').first()
            if last_record and last_record.status == 'IN':
                # User is currently IN, log them OUT
                Attendance.objects.create(rfid_tag=rfid_tag, status='OUT')
                access_message += " You have clocked out."
            else:
                # User is currently OUT, log them IN
                Attendance.objects.create(rfid_tag=rfid_tag, status='IN')
                access_message += " You have clocked in."
        
        except User.DoesNotExist:
            access_message = "Access Denied! Invalid RFID tag."
    
    current_time = timezone.now().strftime("%H:%M:%S")
    current_date = timezone.now().date()
    
    return render(request, 'attendance/scan_rfid.html', {
        'current_time': current_time,
        'current_date': current_date,
        'access_message': access_message
    })