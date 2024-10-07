from django.db.models import Q
from django.db.models.query import QuerySet


class AdSearcher:
    """
    Класс для поиска объявлений на основе частичных совпадений с VIN.
    """

    def __init__(self, queryset: QuerySet, vin_search: str):
        """
        Инициализация объекта поиска объявлений.

        :param queryset: QuerySet с объявлениями, которые будут фильтроваться
        :param vin_search: Строка с VIN, по которым будет производиться поиск
        """
        self.queryset = queryset
        self.vin_search = vin_search

    def search_ads(self) -> QuerySet:
        """
        Выполняет поиск объявлений на основе частичного совпадения с VIN.

        :return: Отфильтрованный QuerySet с объявлениями
        """
        # Разбиваем строку VIN на фрагменты, удаляя пробелы и пустые строки
        vin_search_fragments = [fragment.strip() for fragment in self.vin_search.split(',') if fragment.strip()]

        # Если есть фрагменты для поиска, создаем Q объекты для поиска
        if vin_search_fragments:
            q_objects = Q()  # Создаем пустой Q объект

            # Итерируем по фрагментам и добавляем их в Q объект с условием OR
            for fragment in vin_search_fragments:
                q_objects |= Q(original_vin__icontains=fragment)

            # Фильтруем queryset на основе сформированных Q объектов
            self.queryset = self.queryset.filter(q_objects)

        return self.queryset
