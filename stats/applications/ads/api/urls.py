from django.urls import path
from . import views

urlpatterns = [
    # path('filter-ads/', views.FilterAdsView.as_view(), name='filter_ads'),
    path('marks/', views.MarkListView.as_view(), name='marks-options'),
    path('models/', views.ModelsByMarkView.as_view(), name='models-options'),
    path('modifications/', views.ModificationsByModelView.as_view(), name='modifications-options'),
    path('bodies/', views.BodiesByModelView.as_view(), name='bodies-options'),
    path('complectations/', views.ConfigurationsByModelView.as_view(), name='configurations-options'),
    path('colors/', views.ColorsByModelView.as_view(), name='colors-options'),
]
