from django.urls import path, re_path
from django.contrib import admin

from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', ClientsHome.as_view(), name='home'),
    path('', home, name='home')
]
