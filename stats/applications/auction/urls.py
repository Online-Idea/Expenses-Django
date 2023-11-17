from django.urls import path

from .views import *

urlpatterns = [
    path('auction', auction, name='auction'),
    path('download-auction/', download_auction, name='download_auction'),
]
