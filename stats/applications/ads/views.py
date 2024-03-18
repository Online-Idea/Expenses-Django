import json
from pprint import pprint

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from .models import Ad
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
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.sort_form.fields['fields'].choices = [
            (field.name, field.verbose_name) for field in Ad._meta.get_fields()
        ]
        return queryset

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        print(body_data)
        queryset = self.get_queryset()

        # if 'reset' in body_data:
        #     self.sort_form = self.form_class()
        #     return self.get_ajax_response(self.get_queryset())

        # if 'search' in body_data:
        #     searcher = AdSearcher(self.get_queryset(), body_data['search'].get('vin_search', '').strip())
        #     queryset = searcher.search_ads()
        #     return self.get_ajax_response(queryset)
        for key, value in body_data.items():
            if key == 'sort':
                sorter = AdSorter(self.get_queryset(), value)
                queryset = sorter.sort_ads()
            if key == 'search':
                searcher = AdSearcher(queryset, body_data['search'].get('vin_search', '').strip())
                queryset = searcher.search_ads()

        return self.get_ajax_response(queryset)

        # if 'filter' in request.POST:
        #     filter_ = AdFilter(self.get_queryset(), request.POST.get('value', '').split(','))
        #     filtered_queryset = filter_.filter_ads()
        #     return self.get_ajax_response(filtered_queryset)

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
