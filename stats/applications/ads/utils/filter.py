from applications.ads.api import serializers
from applications.ads.models import Ad
from django.db.models.query import QuerySet


class AdFilter:
    """
    Класс для фильтрации объявлений на основе параметров запроса.
    """

    def __init__(self, queryset: QuerySet, request_param: dict):
        """
        Инициализация фильтра для объявлений.

        :param queryset: QuerySet с объявлениями, которые будут фильтроваться
        :param request_param: Параметры запроса для фильтрации
        """
        self.queryset = queryset
        self.request_param = request_param

    def filter_ads(self) -> QuerySet:
        """
        Фильтрует объявления на основе параметров запроса.

        :return: Отфильтрованный QuerySet с объявлениями
        """
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

        # Итерируем по параметрам запроса и собираем фильтры
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

        # Вывод отладочной информации
        print(f'{filters=}')

        # Применяем фильтры к объявлениям и возвращаем отфильтрованный QuerySet
        filtered_ads = self.queryset.filter(**filters)
        return filtered_ads
