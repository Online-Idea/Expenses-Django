from django.urls import include, path
from rest_framework import routers

from . import ajax_datatable_views
from .views import *

router = routers.DefaultRouter()
router.register(r'api/v1/calls', CallViewSet)

urlpatterns = [
    path('calls', calls, name='calls'),
    path('download_calls', download_calls, name='download_calls'),
    path('calls_pivot', calls_pivot, name='calls_pivot'),
    path('download_calls_pivot', download_calls_pivot, name='download_calls_pivot'),
    path('calls_pivot_custom', calls_pivot_custom, name='calls_pivot_custom'),
    path('ajax_datatable/calls/', ajax_datatable_views.CallDatatableView.as_view(), name='ajax_datatable_calls'),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('calls/new', new_call, name='new_call'),
    path('calls/edit/<int:pk>/', edit_call, name='edit_call'),
    path('calls/delete/<int:pk>/', delete_call, name='delete_call'),
]
