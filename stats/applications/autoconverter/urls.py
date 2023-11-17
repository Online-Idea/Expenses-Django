from django.urls import path

from .views import *


urlpatterns = [
    path('converter', ConverterManual.as_view(), name='converter_manual'),
    path('converter/photo_folders/get', photo_folders, name='get_photo_folders'),
    path('converter/configurations/get', configurations, name='get_configurations'),
]
