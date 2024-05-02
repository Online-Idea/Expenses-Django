from django.urls import path

from .views import *
from . import ajax_datatable_views

urlpatterns = [
    path('ajax_datatable/calls/', ajax_datatable_views.CallDatatableView.as_view(), name='ajax_datatable_calls'),
    path('calls', calls, name='calls'),
]
