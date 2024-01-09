from django.urls import path

from . import ajax_datatable_views
from .views import *

urlpatterns = [
    path('api/v1/autoru_parsed_ads/create', AutoruParsedAdViewSet.as_view({'post': 'create'}), name='autoru_parsed_ads_create'),
    path('parsed_ads', parsed_ads, name='parsed_ads'),
    path('download_parsed_ads', download_parsed_ads, name='download_parsed_ads'),
    path('ajax_datatable/autoru_parsed_ad', ajax_datatable_views.AutoruParsedAdAjaxDatatableView.as_view(),
         name='ajax_datatable_autoru_parsed_ad'),
    path('comparison', comparison, name='comparison'),
    path('download_comparison', download_comparison, name='download_comparison'),
    path('ajax_datatable/comparison', ajax_datatable_views.ComparisonDatatableView.as_view(),
         name='ajax_datatable_comparison'),
    # path('api/get_dealers_for_comparison', get_dealers_for_comparison, name='get_dealers_for_comparison'),
    path('api/v1/dealers_for_srav', DealersForSravView.as_view(), name='dealers_for_srav'),
]
