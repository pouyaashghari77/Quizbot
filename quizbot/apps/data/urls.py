from django.urls import path
from .views import main_webhook

urlpatterns = [
    path('webhook/', main_webhook),
]
