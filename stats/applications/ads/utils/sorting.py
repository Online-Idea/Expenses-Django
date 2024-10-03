from django.db.models.query import QuerySet


class AdSorter:
    """
    Класс для сортировки объявлений на основе параметров запроса.
    """

    def __init__(self, queryset: QuerySet, request_data: dict):
        """
        Инициализация сортировщика объявлений.

        :param queryset: QuerySet с объявлениями, которые будут сортироваться
        :param request_data: Параметры запроса, содержащие поля для сортировки и порядок сортировки
        """
        self.queryset = queryset
        self.request_data = request_data

    def sort_ads(self) -> QuerySet:
        """
        Сортирует объявления на основе данных запроса.

        :return: Отсортированный QuerySet с объявлениями
        """
        # Генерация списка полей для сортировки с учетом порядка (asc/desc)
        for_sorting = [
            f'-{self.request_data[f"field_{i}"]}' if self.request_data[f"order_{i}"] == 'desc'
            else self.request_data[f"field_{i}"]
            for i in range(len(self.request_data) // 2)
        ]

        # Применение сортировки к queryset
        sorted_queryset = self.queryset.order_by(*for_sorting)

        return sorted_queryset
