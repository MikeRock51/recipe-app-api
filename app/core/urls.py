from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path('health-check/', views.health_check, name='health-check'),
]
