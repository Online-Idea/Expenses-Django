from django.urls import path, include

from applications.ads.apps import AdsConfig
from . import views

app_name = AdsConfig.name

urlpatterns = [
    path('salon/<int:pk>/', views.AdListView.as_view(), name='ads'),
    path('detail/<int:pk>/', views.AdDetailView.as_view(), name='ad_detail'),
    path('api/', include('applications.ads.api.urls')),
]