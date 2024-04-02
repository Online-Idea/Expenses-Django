from django.urls import path

from .views import *
from . import ajax_datatable_views

urlpatterns = [
    path('auction', auction, name='auction'),
    path('download-auction/', download_auction, name='download_auction'),
    path('ajax_datatable/auction', ajax_datatable_views.AuctionAjaxDatatableView.as_view(),
         name='ajax_datatable_auction'),
]
