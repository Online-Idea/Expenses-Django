from functools import reduce

from django.http import StreamingHttpResponse, HttpResponse
from lxml import etree

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from applications.ads.models import Ad
from applications.mainapp.models import Model, Mark
from . import serializers


class FilterAdsView(APIView):
    def get(self, request, *args, **kwargs):
        print(request.query_params)
        # Получение параметров фильтрации из запроса
        filters = {}

        # Мапа между ключами из запроса и полями модели
        field_mapping = {
            'marks': 'mark__id',
            'models': 'model__id',
            'modifications': 'modification',
            'bodies': 'body_type',
            'complectations': 'complectation',
            'colors': 'color',
            'priceFrom': 'price__gte',
            'priceTo': 'price__lte',
            'yearFrom': 'year__gte',
            'yearTo': 'year__lte',
            'runFrom': 'run__gte',
            'runTo': 'run__lte',
        }

        # Итерируем по параметрам запроса
        for key in request.query_params:
            values = request.query_params.getlist(key)
            # Пропускаем специальные параметры, которые не являются фильтрами
            if key in ['page', 'format']:
                continue
            # Преобразуем ключ из запроса в соответствующее поле модели, если такое отображение существует
            field_name = field_mapping.get(key)
            if field_name:
                # Если параметр имеет множественное значение, например, марки или модели
                if len(values) > 1:
                    filters[f'{field_name}__in'] = values
                else:
                    # Если параметр имеет одно значение
                    filters[field_name] = values[0]

        # Применяем фильтры к объявлениям
        filtered_ads = Ad.objects.filter(**filters)
        print(filtered_ads)
        serializer = serializers.AdSerializer(filtered_ads, many=True)
        return Response(serializer.data)


class MarkListView(ListAPIView):
    queryset = Mark.objects.filter(ads__isnull=False).distinct()
    serializer_class = serializers.MarkSerializer


class ModelsByMarkView(ListAPIView):
    serializer_class = serializers.ModelSerializer

    def get_queryset(self):
        marks = self.request.query_params.getlist('marks')

        if not marks:
            return Ad.objects.none()

        queryset = Model.objects.filter(ads__mark__id__in=marks).distinct()

        return queryset


class ModificationsByModelView(ListAPIView):
    serializer_class = serializers.ModificationSerializer

    def get_queryset(self):
        models = self.request.query_params.getlist('models')

        if not models:
            return Ad.objects.none()

        queryset = Ad.objects.filter(model__id__in=models).distinct('model__id')
        return queryset


class BodiesByModelView(ListAPIView):
    def list(self, request, *args, **kwargs):
        model_ids = self.request.query_params.getlist('models')
        if not model_ids:
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        bodies = Ad.objects.filter(model_id__in=model_ids).values('body_type').distinct()
        return Response(bodies)


class ConfigurationsByModelView(ListAPIView):
    def list(self, request, *args, **kwargs):
        model_ids = self.request.query_params.getlist('models')
        if not model_ids:
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        configurations = Ad.objects.filter(model_id__in=model_ids).values('complectation').distinct()
        return Response(configurations)


class ColorsByModelView(ListAPIView):
    def list(self, request, *args, **kwargs):
        model_ids = self.request.query_params.getlist('models')
        if not model_ids:
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        colors = Ad.objects.filter(model_id__in=model_ids).values('color').distinct()
        return Response(colors)


class ExportAdsToXMLAPIView(APIView):
    """
    Экспорт объявлений в XML формате через API.
    """

    prefix = """
        Авилон Premium - центр премиальных автомобилей! 
            ✅Более 26 лет на рынке; 
            ✅Автодилер года 2022; 
            ✅ Более 200 новых автомобилей в наличии с ПТС; 
            ✅ Подбор автомобиля по индивидуальному заказу; 
            ✅ Постановка на учёт без вашего присутствия по доверенности; 
            ✅ Специальные условия лизинга от 10 компаний-партнёров; 
            ✅ Честный кредит от 5,6%; 
            ✅ На Ваш выбор 7 лучших страховых компаний; 
            ✅ Детейлинг: защита автомобиля, доработка автомобилей любыми опциями, перешив салона; 
            ✅ Гарантия на все автомобили от 1 до 2 лет; 
            ✅Регулярные поставки новых моделей; 
            ✅ Выгода по trade in до 1 000 000.  
            
    """

    def post(self, request, *args, **kwargs):
        # Получаем параметры из тела запроса
        data = request.query_params.getlist('id')
        queryset = self.apply_filters(data)
        print(data)
        # Создаем корневой элемент XML
        root = etree.Element("data")
        cars = etree.SubElement(root, "cars")

        for ad in queryset:
            self.populate_car_element(cars, ad)

        # Генерируем XML данные
        xml_content = self.generate_xml(root)

        # Возвращаем XML в качестве HTTP ответа
        return HttpResponse(xml_content, content_type='application/xml')

    def apply_filters(self, ids_ad):
        queryset = Ad.objects.filter(id__in=ids_ad)
        return queryset

    def populate_car_element(self, cars, ad):
        """ Заполняет XML элемент данными об объявлении. """
        car = etree.SubElement(cars, "car")
        etree.SubElement(car, "unique_id").text = str(ad.id)
        etree.SubElement(car, "mark_id").text = ad.mark.mark
        etree.SubElement(car, "folder_id").text = str(ad.model.id)
        etree.SubElement(car, "modification_id").text = str(ad.modification)
        etree.SubElement(car, "modification-code").text = ad.modification_code
        etree.SubElement(car, "complectation_name").text = ad.complectation
        etree.SubElement(car, "color-code").text = str(ad.color_code)
        etree.SubElement(car, "interior-code").text = str(ad.interior_code)
        etree.SubElement(car, "equipment-code").text = str(ad.configuration_codes)
        etree.SubElement(car, "body_type").text = str(ad.body_type)
        # etree.SubElement(car, "wheel").text = ad.wheel
        etree.SubElement(car, "color").text = str(ad.color)
        # etree.SubElement(car, "metallic").text = ad.metallic
        etree.SubElement(car, "availability").text = str(ad.get_availability_display())
        # etree.SubElement(car, "custom").text = ad.custom
        etree.SubElement(car, "state").text = str(ad.condition)
        # etree.SubElement(car, "owners_number").text = str(ad.owners_number)
        etree.SubElement(car, "run").text = str(ad.get_run_display())
        etree.SubElement(car, "year").text = str(ad.year)
        etree.SubElement(car, "price").text = str(ad.price)
        etree.SubElement(car, "with_nds").text = 'false' \
            if ad.get_price_nds_display().lower() == 'нет' else 'true'
        etree.SubElement(car, "credit_discount").text = str(ad.credit)
        etree.SubElement(car, "insurance_discount").text = str(ad.insurance)
        etree.SubElement(car, "tradein_discount").text = str(ad.trade_in)
        etree.SubElement(car, "max_discount").text = str(ad.max_discount)
        # etree.SubElement(car, "currency").text = str(ad.currency)
        # etree.SubElement(car, "registry_year").text = str(ad.registry_year)
        etree.SubElement(car, "vin").text = ad.original_vin or "нет VIN"
        # etree.SubElement(car, "action").text = str(ad.action)

        description = etree.SubElement(car, "description")
        description.text = etree.CDATA(ExportAdsToXMLAPIView.prefix + ad.description)

        images = etree.SubElement(car, "images")
        for photo_url in ad.get_photos():
            etree.SubElement(images, "image").text = photo_url

        if ad.video:
            video = etree.SubElement(car, "video")
            video.text = ad.video

        badges = etree.SubElement(car, "badges")
        badge = etree.SubElement(badges, "badge")
        etree.SubElement(badge, "name").text = 'лучшее предложение месяца'

        contact_info = etree.SubElement(car, "contact_info")
        contact = etree.SubElement(contact_info, "contact")
        etree.SubElement(contact, "name"). text = str(ad.salon.name)
        etree.SubElement(contact, "phone").text = str(ad.salon.telephone)
        etree.SubElement(contact, "time").text = str(ad.salon.working_hours)
        etree.SubElement(car, 'poi_id').text = str(ad.salon.address)




    def generate_xml(self, root):
        """ Генерирует XML данные. """
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8', method="xml")
