from django.urls import path

from .views import *

urlpatterns = [
    path('api/get_models_for_mark/<int:mark_id>/', get_models_for_mark, name='get_models_for_mark'),
    path('api/v1/clients/create', ClientCreateAPIView.as_view(), name='clients_create'),
    path('login', LoginUser.as_view(), name='login'),
    path('logout', logout_user, name='logout'),
]
