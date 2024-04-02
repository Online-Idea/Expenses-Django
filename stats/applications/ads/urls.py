from django.urls import path, include

from applications.ads.apps import AdsConfig
from . import views

app_name = AdsConfig.name

urlpatterns = [
    path('ads/', views.AdListView.as_view(), name='ads'),
    path('ad/<int:pk>/', views.AdDetailView.as_view(), name='ad_detail'),
    path('api/', include('applications.ads.api.urls')),
]