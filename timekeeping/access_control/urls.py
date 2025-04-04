from django.urls import path
from .import views

urlpatterns = [
    path('', views.access_control, name='access_control'),
]
