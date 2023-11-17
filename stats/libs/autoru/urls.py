from django.urls import path

from .views import *

urlpatterns = [
    path('autoru_catalog', autoru_catalog, name='autoru_catalog'),
    path('autoru_regions', autoru_regions, name='autoru_regions'),
]