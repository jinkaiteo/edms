"""
Settings URL Configuration
"""
from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('email/send-test/', views.send_test_email, name='send-test-email'),
]
