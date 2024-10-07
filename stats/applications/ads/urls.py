from django.urls import path, include

from applications.ads.apps import AdsConfig
from . import views

# Установка пространства имен для приложения
app_name = AdsConfig.name

urlpatterns = [
    # Маршрут для отображения списка объявлений по ID салона
    path('salon/<int:pk>/', views.AdListView.as_view(), name='ads'),

    # Маршрут для отображения деталей объявления по ID
    path('detail/<int:pk>/', views.AdDetailView.as_view(), name='ad_detail'),

    # Включение маршрутов API для приложения ads
    path('api/', include('applications.ads.api.urls')),
]
