class AdSorter:
    def __init__(self, queryset, request_data):
        self.queryset = queryset
        self.request_data = request_data

    def sort_ads(self):
        for_sorting = [f'-{self.request_data[f"field_{i}"]}'
                       if self.request_data[f"order_{i}"] == 'desc'
                       else self.request_data[f"field_{i}"]
                       for i in range(len(self.request_data) // 2)]
        print(for_sorting)
        sorted_queryset = self.queryset.order_by(*for_sorting)

        return sorted_queryset
