from django.urls import path

from . import ajax_datatable_views
from .views import *

urlpatterns = [
    path('api/v1/autoru_parsed_ads/create', AutoruParsedAdViewSet.as_view({'post': 'create'}), name='autoru_parsed_ads_create'),
    path('srav', srav, name='srav'),
    path('download-srav', download_srav, name='download_srav'),
    path('ajax_datatable/autoru_parsed_ad/', ajax_datatable_views.AutoruParsedAdAjaxDatatableView.as_view(),
         name='ajax_datatable_autoru_parsed_ad')
]
