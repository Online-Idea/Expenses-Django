from django.urls import include, path
from rest_framework import routers

from .serializers import CallSerializer
from .views import *
from . import ajax_datatable_views

router = routers.DefaultRouter()
router.register(r'api/v1/calls', CallViewSet)

urlpatterns = [
    path('calls', calls, name='calls'),
    path('ajax_datatable/calls/', ajax_datatable_views.CallDatatableView.as_view(), name='ajax_datatable_calls'),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('calls/edit/<int:pk>/', edit_call, name='edit_call'),
]
