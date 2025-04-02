from django.utils import timezone
from django.http import JsonResponse
from .models import TimeEntry
from django.contrib.auth.models import User

# Set a threshold for the time difference (e.g., 5 seconds)
TIME_THRESHOLD = 5 # Seconds

def log_time_entry(request):
    if request.method =='POST':
        rfid_tag = request.POST.get('rfid_tag')
        user = User.objects.get(rfid_tag=rfid_tag)     # Assuming you have a way to get the user by RFID

        # Get the last itme entry for the user
        last_entry = TimeEntry.objects.filter(user=user).order_by('-timestamp').first()

        # Check if the last entry exists and if the time difference is within the threshold
        if last_entry:
            time_difference = (timezone.now() - last_entry.timestamp).total_seconds()
            if time_difference < TIME_THRESHOLD:
                return JsonResponse({'status': 'ignored', 'message': 'Duplicate entry ignored.'})
            
        # Log the new time entry
        TimeEntry.objects.create(user=user)
        return JsonResponse({'status': 'success', 'message': 'Time entry logged.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})