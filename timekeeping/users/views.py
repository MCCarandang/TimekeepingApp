from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def users_view(request):
    return HttpResponse("User list will be displayed here.")