from django.urls import path
from . import views

urlpatterns = [
    path('', views.users_view, name = "users"),
]