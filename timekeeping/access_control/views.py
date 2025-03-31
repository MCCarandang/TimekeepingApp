from django.shortcuts import render
from .models import User

# This is to handle access granted and denied scenarios

def access_control(request):
    if request.method == 'POST':
        rfid_tag = request.POST.get('rfid_tag')
        try:
            user = User.objects.get(rfid_tag=rfid_tag)
            return render(request, 'access_control/access_granted.html', {'user': user})
        except User.DoesNotExist:
            return render(request, 'access_control/access_denied.html')
    return render(request, 'access_control/index.html')