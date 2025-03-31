from django.shortcuts import render
from django.http import JsonResponse  # To return JSON responses
from .models import Attendance      #imports the models.py from attendance app
from django.utils import timezone
import pytz

# Create your views here.
def home(request):
    current_time_utc = timezone.now()

    # Convert to Philippine Time
    philippine_tz = pytz.timezone('Asia/Manila')
    current_time = current_time_utc.astimezone(philippine_tz)

    current_date = current_time.date()  # Get the date
    current_time_only = current_time.time() # Get the time
    return render(request, 'attendance/home.html', {
        'current_date': current_date,
        'current_time': current_time_only
        })  # Gets the current date and time using Django's timezone.now(). This ensures time is stored in a timezone-aware format.

def check_in_out(user_id):
    last_record = Attendance.objects.filter(rfid_tag=user_id).order_by('timestamp').first()
    if last_record and last_record.status == 'IN':
        # User is currently IN, so we log them OUT
        Attendance.objects.create(rfid_tag=user_id, status='OUT')
        return 'OUT'
    else:
        # User is currently OUT, so we log them IN
        Attendance.objects.create(rfid_tag=user_id, status='IN')
        return 'IN'
    
# Django view that calls check_in_out()
def record_attnedance(request):
    if request.method == 'POST':
        rfid_tag = request.POST.get('rfid_tag')
        status = check_in_out('rfid_tag')  # call the function to checkin/out
        current_time = timezone.now()   # Get the current time

        return JsonResponse({'rfid_tag': rfid_tag, 'status':status, 'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S")})  # Return JSON response
    return JsonResponse({'error': 'Invalid request'}, status=400)