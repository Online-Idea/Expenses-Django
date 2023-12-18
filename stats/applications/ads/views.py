from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.views.generic import ListView, DetailView
from .models import Ad
from .forms import SortForm
from pprint import pprint


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
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.sort_form.fields['fields'].choices = [
            (field.name, field.verbose_name) for field in Ad._meta.get_fields()
        ]
        return queryset

    def post(self, request, *args, **kwargs):
        if 'apply-sort' in request.POST:
            # Логика формирования списка для сортировки
            for_sorting = [f'-{request.POST[f"field_{i}"]}'
                           if request.POST[f"order_{i}"] == 'desc'
                           else request.POST[f"field_{i}"]
                           for i in range(len(request.POST) // 2)]

            # Выполняем сортировку
            queryset = self.get_queryset()
            sorted_queryset = queryset.order_by(*for_sorting)

            # Возвращаем JSON с отсортированным queryset
            response_data = {
                'html': render_to_string('ads/ads_block.html', {'ads': sorted_queryset}, request),
                'success': True,
            }
            return JsonResponse(response_data)

        if 'reset-sort' in request.POST:
            queryset = self.get_queryset()
            sorted_queryset = queryset
            # Очищаем таблицу
            self.sort_form = self.form_class()  # Обнуляем форму сортировки
            # Возвращаем карточки в изначальный порядок
            response_data = {
                'html': render_to_string('ads/ads_block.html', {'ads': sorted_queryset}, request),
                'success': True,
            }
            return JsonResponse(response_data)

        if 'apply-search' in request.POST:
            vin_search = request.POST.get('vin_search', '').strip()
            queryset = self.get_queryset()
            print(vin_search, queryset, '*' * 100)
            if vin_search:
                queryset = queryset.filter(vin__icontains=vin_search)
                print(vin_search, queryset, '*' * 100)


            response_data = {
                'html': render_to_string('ads/ads_block.html', {'ads': queryset}, request),
                'success': True,
            }
            return JsonResponse(response_data)


class AdDetailView(DetailView):
    model = Ad
    template_name = 'ads/ad_detail.html'
    context_object_name = 'ad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['additional_photos_enum'] = self.object.get_additional_photos_enum()
        return context
