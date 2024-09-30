import json
from pprint import pprint

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from .forms import SortForm

from typing import Any, Dict, List
from django.http import HttpRequest, HttpResponse
from django.views import View
from lxml import etree
import json
from .models import Ad, Salon

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
        context['marks'] = Ad.objects.values_list('mark__id', 'mark__name').distinct()
        context['salons'] = Salon.objects.all()
        salon_id = kwargs.get('pk')
        if salon_id:
            context['ads'] = context['ads'].filter(salon_id=salon_id)
            context['salon'] = get_object_or_404(Salon, id=salon_id)
        else:
            context['salon'] = None
        return context

    # def get_queryset(self):
    #     self.original_queryset = super().get_queryset()
    #     self.sort_form.fields['fields'].choices = [
    #         ('mark', 'Марка'),
    #         ('model', 'Модель',),
    #         ('complectation', 'Комплектация',),
    #         ('price', 'Цена',),
    #         ('body_type', 'Кузов',),
    #         ('year', 'Год',),
    #         ('color', 'Цвет',),
    #         ('price_nds', 'Цена c НДС'),
    #         ('engine_capacity', 'Объём двигателя',),
    #         ('run', 'Пробег',),
    #         ('engine_capacity', 'Мощность',),
    #         ('drive', 'Привод',),
    #         ('datetime_created', 'Дата создания',)
    #     ]
    #     return self.original_queryset

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        self.original_queryset = super().get_queryset()
        print(f'{body_data=}')
        self.get_queryset()
        salon_id = body_data.get('salon_id')  # Пытаемся получить salon_id из POST-запроса
        print(f'{salon_id=}')
        if salon_id:
            self.original_queryset = self.original_queryset.filter(salon_id=salon_id)
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


class ExportAdsToXMLView(View):
    """ Экспорт объявлений в XML формате. """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        data: Dict = json.loads(request.body)
        queryset = self.apply_filters(data)

        root = etree.Element("data")
        cars = etree.SubElement(root, "cars")

        for ad in queryset:
            car = etree.SubElement(cars, "car")
            self.populate_car_element(car, ad)

        response = HttpResponse(content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="ads.xml"'
        tree = etree.ElementTree(root)
        tree.write(response, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return response

    def apply_filters(self, filters: Dict) -> List[Ad]:
        """ Применяет фильтры к модели Ad. """
        queryset = Ad.objects.all()
        # Применяем фильтрацию согласно переданным параметрам (пример):
        # if 'year' in filters:
        #     queryset = queryset.filter(year=filters['year'])
        return queryset

    def populate_car_element(self, car: etree._Element, ad: Ad) -> None:
        """ Заполняет XML элемент данными об объявлении. """
        etree.SubElement(car, "unique_id").text = str(ad.id)
        etree.SubElement(car, "mark_id").text = ad.mark.name
        etree.SubElement(car, "folder_id").text = str(ad.model.id)
        etree.SubElement(car, "modification_id").text = ad.modification_autoru or "не указано"
        etree.SubElement(car, "complectation_name").text = ad.configuration_autoru or "стандарт"
        etree.SubElement(car, "body_type").text = ad.body_type
        etree.SubElement(car, "year").text = str(ad.year)
        etree.SubElement(car, "color").text = ad.color
        etree.SubElement(car, "metallic").text = "да" if ad.is_metallic else "нет"
        etree.SubElement(car, "price").text = ad.get_price_display()
        etree.SubElement(car, "with_nds").text = "true" if ad.price_nds == "Да" else "false"
        etree.SubElement(car, "availability").text = ad.get_availability_display()
        etree.SubElement(car, "vin").text = ad.vin or "нет VIN"

        description = etree.SubElement(car, "description")
        description.text = etree.CDATA(ad.description)

        images = etree.SubElement(car, "images")
        for photo_url in ad.get_photos():
            etree.SubElement(images, "image").text = photo_url

        video = etree.SubElement(car, "video")
        video.text = ad.video or "нет видео"

        extras = etree.SubElement(car, "extras")
        extras.text = ", ".join(ad.get_configuration_codes()) or "нет дополнений"
