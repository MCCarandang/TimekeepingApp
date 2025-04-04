from django.urls import path
from . import views

urlpatterns = [
    path('', views.scan_rfid, name='scan_rfid'),
]