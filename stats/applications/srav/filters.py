import django_filters
from .models import AutoruParsedAd


class AutoruParsedAdFilter(django_filters.FilterSet):
    datetime = django_filters.DateFromToRangeFilter()
    region = django_filters.CharFilter(lookup_expr='icontains')
    mark = django_filters.CharFilter(field_name='mark__name', lookup_expr='exact')
    model = django_filters.CharFilter(field_name='model__name', lookup_expr='exact')

    class Meta:
        model = AutoruParsedAd
        fields = ['datetime', 'region', 'mark', 'model']
