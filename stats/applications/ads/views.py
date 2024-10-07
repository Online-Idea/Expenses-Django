import json
from pprint import pprint

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from django.http import HttpRequest, HttpResponse
from django.views import View
from lxml import etree
from typing import Any, Dict, List

from .forms import SortForm
from .models import Ad, Salon
from .utils.filter import AdFilter
from .utils.search import AdSearcher
from .utils.sorting import AdSorter


class AdListView(ListView):
    """
    Вью для отображения списка объявлений с поддержкой фильтрации, сортировки и поиска.
    """
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ads'
    form_class = SortForm
    sort_form = form_class()
    original_queryset = None

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Возвращает контекст данных для рендера шаблона.
        Добавляет форму сортировки, список марок и салонов, а также фильтрует объявления по салону, если указан ID салона.
        """
        # Получаем стандартные данные контекста
        context = super().get_context_data(**kwargs)

        # Добавляем форму сортировки в контекст
        context['sort_form'] = self.sort_form

        # Получаем список уникальных марок для фильтрации и добавляем в контекст
        context['marks'] = Ad.objects.values_list('mark__id', 'mark__name').distinct()

        # Получаем список всех салонов для отображения в фильтре
        context['salons'] = Salon.objects.all()

        # Получаем ID салона из kwargs (если передан)
        salon_id = kwargs.get('pk')
        if salon_id:
            # Если салон указан, фильтруем объявления по этому салону
            context['ads'] = context['ads'].filter(salon_id=salon_id)

            # Добавляем выбранный салон в контекст
            context['salon'] = get_object_or_404(Salon, id=salon_id)
        else:
            # Если салон не указан, контекст 'salon' остается None
            context['salon'] = None

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Обрабатывает POST-запрос, применяя фильтры, сортировку и поиск к объявлениям.
        Возвращает данные через AJAX.
        """
        # Читаем тело запроса, преобразуя его из JSON
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # Получаем исходный QuerySet объявлений
        self.original_queryset = super().get_queryset()

        # Проверяем, был ли передан ID салона для фильтрации
        salon_id = body_data.get('salon_id')
        if salon_id:
            # Если салон указан, фильтруем объявления по salon_id
            self.original_queryset = self.original_queryset.filter(salon_id=salon_id)

        # Обрабатываем фильтры, сортировку и поиск на основе переданных данных
        for key, value in body_data.items():
            if key == 'sort':
                # Если требуется сортировка, создаем AdSorter и применяем его
                sorter = AdSorter(self.original_queryset, value)
                self.original_queryset = sorter.sort_ads()
            elif key == 'search':
                # Если требуется поиск, создаем AdSearcher и применяем его
                searcher = AdSearcher(self.original_queryset, value.get('vin_search', '').strip())
                self.original_queryset = searcher.search_ads()
            elif key == 'filters':
                # Если требуются фильтры, создаем AdFilter и применяем его
                ad_filter = AdFilter(self.original_queryset, value)
                self.original_queryset = ad_filter.filter_ads()

        # Возвращаем ответ через AJAX с отфильтрованными и отсортированными данными
        return self.get_ajax_response(self.original_queryset)

    def get_ajax_response(self, queryset: List[Ad]) -> JsonResponse:
        """
        Возвращает отфильтрованные и отсортированные объявления через AJAX в виде HTML блока.
        """
        # Рендерим HTML блок с объявлениями и добавляем его в ответ
        html = render_to_string('ads/ads_block.html', {'ads': queryset}, self.request)
        response_data = {
            'html': html,
            'success': True,
        }
        return JsonResponse(response_data)


class AdDetailView(DetailView):
    """
    Вью для отображения деталей одного объявления.
    """
    model = Ad
    template_name = 'ads/ad_detail.html'
    context_object_name = 'ad'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Возвращает контекст данных для рендера шаблона деталей объявления.
        Добавляет фотографии объявления в контекст.
        """
        # Получаем стандартные данные контекста
        context = super().get_context_data(**kwargs)

        # Добавляем фотографии в контекст, используя метод get_photos_enum()
        context['photos_enum'] = self.object.get_photos_enum()

        return context


class ExportAdsToXMLView(View):
    """
    Вью для экспорта списка объявлений в XML формате.
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Обрабатывает POST-запрос для экспорта объявлений в формате XML.
        Применяет фильтры и формирует XML документ с объявлениями.
        """
        # Читаем и преобразуем тело запроса из JSON
        data: Dict = json.loads(request.body)

        # Применяем фильтры к объявлениям
        queryset = self.apply_filters(data)

        # Создаем корневой XML элемент <data> и дочерний элемент <cars>
        root = etree.Element("data")
        cars = etree.SubElement(root, "cars")

        # Заполняем XML данными об объявлениях
        for ad in queryset:
            car = etree.SubElement(cars, "car")
            self.populate_car_element(car, ad)

        # Создаем HTTP ответ с заголовком для загрузки файла XML
        response = HttpResponse(content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="ads.xml"'

        # Записываем XML данные в ответ
        tree = etree.ElementTree(root)
        tree.write(response, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        return response

    def apply_filters(self, filters: Dict) -> List[Ad]:
        """
        Применяет фильтры к объявлениям на основе данных запроса.
        Возвращает отфильтрованный список объявлений.
        """
        queryset = Ad.objects.all()

        # Пример: можно применять фильтры, если переданы соответствующие параметры
        # if 'year' in filters:
        #     queryset = queryset.filter(year=filters['year'])

        return queryset

    def populate_car_element(self, car: etree._Element, ad: Ad) -> None:
        """
        Заполняет XML элемент <car> данными о конкретном объявлении.
        """
        # Добавляем основные данные об объявлении в XML
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

        # Добавляем описание объявления в CDATA
        description = etree.SubElement(car, "description")
        description.text = etree.CDATA(ad.description)

        # Добавляем список фотографий
        images = etree.SubElement(car, "images")
        for photo_url in ad.get_photos():
            etree.SubElement(images, "image").text = photo_url

        # Добавляем видео, если оно есть
        video = etree.SubElement(car, "video")
        video.text = ad.video or "нет видео"

        # Добавляем дополнительные опции (если есть)
        extras = etree.SubElement(car, "extras")
        extras.text = ", ".join(ad.get_configuration_codes()) or "нет дополнений"
