from django.urls import path

from .views import *

urlpatterns = [
    path('netcost', home, name='home'),
]
