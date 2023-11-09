from django.urls import path
from django.contrib import admin

from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', ClientsHome.as_view(), name='home'),
    path('', home, name='home'),
    # re_path(r'^stats/autoru_products/get(?P<from_>)(?P<to>)(?P<client>)$', autoru_products, name='get_autoru_products'),
    path('converter', ConverterManual.as_view(), name='converter_manual'),
    path('auction', auction, name='auction'),
    path('download-auction/', download_auction, name='download_auction'),
    # TODO добавь ссылки ниже на страницу converter
    path('converter/photo_folders/get', photo_folders, name='get_photo_folders'),
    path('converter/configurations/get', configurations, name='get_configurations'),
    path('autoru_catalog', autoru_catalog, name='autoru_catalog'),
    path('autoru_regions', autoru_regions, name='autoru_regions'),
    path('api/get_models_for_mark/<int:mark_id>/', get_models_for_mark, name='get_models_for_mark'),
    path('api/v1/clients/create', ClientsCreateAPIView.as_view(), name='clients_create'),
    path('api/v1/autoru_parsed_ads/create', AutoruParsedAdsViewSet.as_view({'post': 'create'}), name='autoru_parsed_ads_create'),
]
