import json

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from .models import Ad, Salon
from .forms import SortForm

from .utils.filter import AdFilter
from .utils.search import AdSearcher
from .utils.sorting import AdSorter


class AdListView(ListView):
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ads'
    form_class = SortForm

    sort_form = form_class()
    original_queryset = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_form'] = self.sort_form
        context['marks'] = Ad.objects.values_list('mark__id', 'mark__mark').distinct()
        context['salons'] = Salon.objects.all()
        return context

    def get_queryset(self):
        self.original_queryset = super().get_queryset()
        self.sort_form.fields['fields'].choices = [
            (field.name, field.verbose_name) for field in Ad._meta.get_fields()
        ]
        return self.original_queryset

    def get(self, request, *args, **kwargs):
        salon_id = kwargs.get('pk')
        self.get_queryset()
        print(salon_id)
         # Пытаемся получить salon_id из POST-запроса
        if salon_id:
            self.original_queryset = self.original_queryset.filter(salon_id=salon_id)
            salon = get_object_or_404(Salon, id=salon_id)
            # ads = Ad.objects.filter(salon=salon)
            print(self.original_queryset)
        return render(request, 'ads/ad_list.html', {'ads': self.original_queryset, 'salon': salon})
        # return self.get_ajax_response(self.original_queryset)

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # print(body_data)
        # self.get_queryset()
        # salon_id = body_data.get('salon_id')  # Пытаемся получить salon_id из POST-запроса
        # if salon_id:
        #     self.original_queryset = self.original_queryset.filter(salon_id=salon_id)
            # Фильтруем объявления по выбранному салону
        for key, value in body_data.items():
            if key == 'sort':
                sorter = AdSorter(self.original_queryset, value)
                self.original_queryset = sorter.sort_ads()
            if key == 'search':
                searcher = AdSearcher(self.original_queryset, value.get('vin_search', '').strip())
                self.original_queryset = searcher.search_ads()
            if key == 'filters':
                filter = AdFilter(self.original_queryset, value)
                self.original_queryset = filter.filter_ads()
        return self.get_ajax_response(self.original_queryset)

    def get_ajax_response(self, queryset):
        html = render_to_string('ads/ads_block.html', {'ads': queryset}, self.request)
        response_data = {
            'html': html,
            'success': True,
        }
        return JsonResponse(response_data)


class AdDetailView(DetailView):
    model = Ad
    template_name = 'ads/ad_detail.html'
    context_object_name = 'ad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos_enum'] = self.object.get_photos_enum()
        return context
