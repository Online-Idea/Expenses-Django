from django.db.models import Q


class AdSearcher:
    def __init__(self, queryset, vin_search):
        self.queryset = queryset
        self.vin_search = vin_search

    def search_ads(self):
        vin_search_fragments = [fragment.strip() for fragment in self.vin_search.split(',') if fragment.strip()]

        if vin_search_fragments:
            q_objects = Q()
            for fragment in vin_search_fragments:
                q_objects |= Q(original_vin__icontains=fragment)

            self.queryset = self.queryset.filter(q_objects)

        return self.queryset
