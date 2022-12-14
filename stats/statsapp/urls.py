from django.urls import path, re_path
from django.contrib import admin

from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', ClientsHome.as_view(), name='home'),
    path('', home, name='home'),
    # re_path(r'^stats/autoru_products/get(?P<from_>)(?P<to>)(?P<client>)$', autoru_products, name='get_autoru_products'),
    path('converter/photo_folders/get', photo_folders, name='get_photo_folders'),
    path('converter/configurations/get', configurations, name='get_configurations'),
    path('converter/testing', converter_testing, name='converter_testing'),
]
