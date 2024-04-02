from applications.ads.api import serializers
from applications.ads.models import Ad


class AdFilter:
    def __init__(self, queryset, request_param):
        self.queryset = queryset
        self.request_param = request_param

    def filter_ads(self):

        filters = {}

        # Мапа между ключами из запроса и полями модели
        field_mapping = {
            'marks': 'mark__id',
            'models': 'model__id',
            'modifications': 'modification',
            'bodies': 'body_type',
            'complectations': 'complectation',
            'colors': 'color',
            'priceFrom': 'price__gte',
            'priceTo': 'price__lte',
            'yearFrom': 'year__gte',
            'yearTo': 'year__lte',
            'runFrom': 'run__gte',
            'runTo': 'run__lte',
        }

        # Итерируем по параметрам запроса
        for key, values in self.request_param.items():
            # Пропускаем специальные параметры, которые не являются фильтрами
            if key in ['page', 'format']:
                continue
            # Преобразуем ключ из запроса в соответствующее поле модели, если такое отображение существует
            field_name = field_mapping.get(key)
            if field_name:
                # Если параметр имеет множественное значение, например, марки или модели
                if len(values) > 1:
                    filters[f'{field_name}__in'] = values
                else:
                    # Если параметр имеет одно значение
                    filters[field_name] = values[0]

        print(filters)
        # Применяем фильтры к объявлениям
        filtered_ads = self.queryset.filter(**filters)
        # print(filtered_ads)
        # serializer = serializers.AdSerializer(filtered_ads, many=True)
        return filtered_ads
