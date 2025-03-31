from django.urls import path
from .views import access_control

urlpatterns = [
    path('', access_control, name='access_control'),
]
