from applications.ads.models import Ad


class AdFilter:
    def __init__(self, queryset, selected_mark_ids):
        self.queryset = queryset
        self.selected_mark_ids = selected_mark_ids

    def filter_ads(self):
        self.queryset = Ad.objects.filter(mark__id__in=self.selected_mark_ids)
        return self.queryset
