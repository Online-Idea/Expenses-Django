from django.urls import path
from .views import TransportCheckView

urlpatterns = [
    path('transport-check', TransportCheckView.as_view(), name='transport_check'),
]