from django.urls import path
from . import views

urlpatterns = [
    # path('filter-ads/', views.FilterAdsView.as_view(), name='filter_ads'),

    # Маршрут для получения списка всех марок
    path('marks/', views.MarkListView.as_view(), name='marks-options'),

    # Маршрут для получения моделей по выбранной марке
    path('models/', views.ModelsByMarkView.as_view(), name='models-options'),

    # Маршрут для получения модификаций по выбранной модели
    path('modifications/', views.ModificationsByModelView.as_view(), name='modifications-options'),

    # Маршрут для получения типов кузовов по выбранной модели
    path('bodies/', views.BodiesByModelView.as_view(), name='bodies-options'),

    # Маршрут для получения комплектаций по выбранной модели
    path('complectations/', views.ConfigurationsByModelView.as_view(), name='configurations-options'),

    # Маршрут для получения цветов по выбранной модели
    path('colors/', views.ColorsByModelView.as_view(), name='colors-options'),

    # Маршрут для экспорта объявлений в XML
    path('export-xml/', views.ExportAdsToXMLAPIView.as_view(), name='export-ads-xml'),
]
