from django.urls import path
from .views import time_entries_list

urlpatterns = [
    path('time-entries/', time_entries_list, name='time_entries_list'),
]
