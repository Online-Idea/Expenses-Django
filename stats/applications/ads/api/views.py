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
    """
    Вью для фильтрации объявлений на основе параметров запроса.
    """

    def get(self, request, *args, **kwargs) -> Response:
        """
        Обрабатывает GET-запрос и фильтрует объявления по переданным параметрам запроса.

        :param request: объект запроса с фильтрационными параметрами
        :return: отфильтрованные данные в формате JSON
        """
        # Инициализируем пустой словарь для хранения фильтров
        filters = {}

        # Мапа для сопоставления параметров запроса с полями модели
        field_mapping = {
            'marks': 'mark__id',
            'models': 'model__id',
            'modifications': 'modification',
            'bodies': 'body_type',
            'complectations': 'complectation',
            'colors': 'color',
            'priceFrom': 'price__gte',  # фильтр по минимальной цене
            'priceTo': 'price__lte',  # фильтр по максимальной цене
            'yearFrom': 'year__gte',  # фильтр по минимальному году
            'yearTo': 'year__lte',  # фильтр по максимальному году
            'runFrom': 'run__gte',  # фильтр по минимальному пробегу
            'runTo': 'run__lte',  # фильтр по максимальному пробегу
        }

        # Итерируем по параметрам запроса и сопоставляем их с полями модели
        for key in request.query_params:
            values = request.query_params.getlist(key)
            if key in ['page', 'format']:
                # Пропускаем специальные параметры, которые не используются для фильтрации
                continue
            field_name = field_mapping.get(key)
            if field_name:
                # Если значение представляет собой список, используем фильтр "__in", иначе простое присваивание
                if len(values) > 1:
                    filters[f'{field_name}__in'] = values
                else:
                    filters[field_name] = values[0]

        # Применяем фильтры к объектам модели Ad и сериализуем их для возврата в формате JSON
        filtered_ads = Ad.objects.filter(**filters)
        serializer = serializers.AdSerializer(filtered_ads, many=True)
        return Response(serializer.data)


class MarkListView(ListAPIView):
    """
    Вью для получения списка марок с возможной фильтрацией по salon_id.
    """
    serializer_class = serializers.MarkSerializer
    pagination_class = None
    def get_queryset(self):
        """
        Возвращает уникальный список марок с фильтрацией по salon_id, если он указан.

        :return: QuerySet с уникальными марками
        """
        salon_id = self.request.query_params.getlist('salon_id')
        # Получаем уникальные марки, связанные с объявлениями
        queryset = Mark.objects.filter(ads__isnull=False).distinct()
        if salon_id:
            # Фильтруем по salon_id, если он указан
            salon_id = int(salon_id[0])
            queryset = queryset.filter(ads__salon_id=salon_id)
            print(f'{queryset=}')
        return queryset


class ModelsByMarkView(ListAPIView):
    """
    Вью для получения списка моделей по выбранной марке с возможной фильтрацией по salon_id.
    """
    serializer_class = serializers.ModelSerializer
    pagination_class = None

    def get_queryset(self):
        """
        Возвращает уникальный список моделей по выбранной марке и фильтрует по salon_id, если он указан.

        :return: QuerySet с уникальными моделями
        """
        salon_id = self.request.query_params.getlist('salon_id')
        marks = self.request.query_params.getlist('marks')

        if not marks:
            # Если марки не указаны, возвращаем пустой QuerySet
            return Ad.objects.none()

        # Получаем модели, соответствующие переданным маркам
        queryset = Model.objects.filter(ads__mark__id__in=marks).distinct()
        if salon_id:
            # Фильтруем по salon_id, если он указан
            salon_id = int(salon_id[0])
            queryset = queryset.filter(ads__salon_id=salon_id)

        return queryset


class ModificationsByModelView(ListAPIView):
    """
    Вью для получения списка модификаций по выбранной модели с возможной фильтрацией по salon_id.
    """
    serializer_class = serializers.ModificationSerializer
    pagination_class = None

    def get_queryset(self):
        """
        Возвращает уникальный список модификаций по модели и фильтрует по salon_id, если он указан.

        :return: QuerySet с уникальными модификациями
        """
        salon_id = self.request.query_params.getlist('salon_id')
        models = self.request.query_params.getlist('models')

        if not models:
            # Если модели не указаны, возвращаем пустой QuerySet
            return Ad.objects.none()

        # Фильтруем объявления по моделям
        queryset = Ad.objects.filter(model__id__in=models).distinct()
        if salon_id:
            # Фильтруем по salon_id, если он указан
            salon_id = int(salon_id[0])
            queryset = queryset.filter(salon_id=salon_id)

        return queryset


class BodiesByModelView(ListAPIView):
    """
    Вью для получения списка типов кузовов по выбранной модели и salon_id.
    """

    def list(self, request, *args, **kwargs) -> Response:
        """
        Возвращает список уникальных типов кузовов по модели и фильтрует по salon_id, если он указан.

        :param request: объект запроса с параметрами
        :return: JSON с уникальными типами кузовов
        """
        salon_id = self.request.query_params.getlist('salon_id')
        model_ids = self.request.query_params.getlist('models')

        if not model_ids:
            # Если модели не указаны, возвращаем ошибку 400
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Если указан salon_id, фильтруем объявления по нему
        if salon_id:
            salon_id = int(salon_id[0])

        # Получаем уникальные типы кузовов для указанных моделей
        bodies = Ad.objects.filter(model_id__in=model_ids, salon_id=salon_id).values('body_type').distinct()
        return Response(bodies)


class ConfigurationsByModelView(ListAPIView):
    """
    Вью для получения списка комплектаций по выбранной модели.
    """

    def list(self, request, *args, **kwargs) -> Response:
        """
        Возвращает список уникальных комплектаций по модели и фильтрует по salon_id, если он указан.

        :param request: объект запроса с параметрами
        :return: JSON с уникальными комплектациями
        """
        salon_id = self.request.query_params.getlist('salon_id')
        model_ids = self.request.query_params.getlist('models')

        if not model_ids:
            # Если модели не указаны, возвращаем ошибку 400
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Если указан salon_id, фильтруем объявления по нему
        if salon_id:
            salon_id = int(salon_id[0])

        # Получаем уникальные комплектации для указанных моделей
        configurations = Ad.objects.filter(model_id__in=model_ids, salon_id=salon_id).values('complectation').distinct()
        return Response(configurations)


class ColorsByModelView(ListAPIView):
    """
    Вью для получения списка уникальных цветов по выбранной модели.
    """

    def list(self, request, *args, **kwargs) -> Response:
        """
        Возвращает список уникальных цветов по модели и фильтрует по salon_id, если он указан.

        :param request: объект запроса с параметрами
        :return: JSON с уникальными цветами
        """
        salon_id = self.request.query_params.getlist('salon_id')
        model_ids = self.request.query_params.getlist('models')

        if not model_ids:
            # Если модели не указаны, возвращаем ошибку 400
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Если указан salon_id, фильтруем объявления по нему
        if salon_id:
            salon_id = int(salon_id[0])

        # Получаем уникальные цвета для указанных моделей
        colors = Ad.objects.filter(model_id__in=model_ids, salon_id=salon_id).values('color').distinct()
        return Response(colors)


class ExportAdsToXMLAPIView(APIView):
    """
    APIView для экспорта объявлений в формате XML.
    """

    # Префикс, который добавляется в описание объявления в XML
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

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """
        Обрабатывает POST-запрос для экспорта объявлений в формате XML.

        :param request: объект запроса с параметрами
        :return: XML документ с объявлениями
        """
        # Получаем список ID объявлений для экспорта
        data = request.query_params.getlist('id')

        # Применяем фильтры для получения объявлений по ID
        queryset = self.apply_filters(data)

        # Создаем корневой элемент XML
        root = etree.Element("data")
        cars = etree.SubElement(root, "cars")

        # Заполняем XML данными о каждом объявлении
        for ad in queryset:
            self.populate_car_element(cars, ad)

        # Генерация и возврат XML контента
        xml_content = self.generate_xml(root)
        return HttpResponse(xml_content, content_type='application/xml')

    def apply_filters(self, ids_ad: list[str]) -> 'QuerySet[Ad]':
        """
        Применяет фильтры по списку ID объявлений.

        :param ids_ad: список ID объявлений
        :return: отфильтрованный QuerySet
        """
        # Фильтруем объявления по списку ID
        queryset = Ad.objects.filter(id__in=ids_ad)
        return queryset

    def populate_car_element(self, cars: etree.Element, ad: Ad) -> None:
        """
        Заполняет XML элемент данными об одном объявлении.

        :param cars: XML элемент для хранения данных о машинах
        :param ad: объект объявления
        """
        # Создаем элемент <car> и заполняем его данными об объявлении
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
        etree.SubElement(car, "color").text = str(ad.color)
        etree.SubElement(car, "availability").text = str(ad.get_availability_display())
        etree.SubElement(car, "state").text = str(ad.condition)
        etree.SubElement(car, "run").text = str(ad.get_run_display())
        etree.SubElement(car, "year").text = str(ad.year)
        etree.SubElement(car, "price").text = str(ad.price)
        etree.SubElement(car, "with_nds").text = 'false' if ad.get_price_nds_display().lower() == 'нет' else 'true'
        etree.SubElement(car, "credit_discount").text = str(ad.credit)
        etree.SubElement(car, "insurance_discount").text = str(ad.insurance)
        etree.SubElement(car, "tradein_discount").text = str(ad.trade_in)
        etree.SubElement(car, "max_discount").text = str(ad.max_discount)
        etree.SubElement(car, "vin").text = ad.original_vin or "нет VIN"

        # Добавляем описание объявления с префиксом
        description = etree.SubElement(car, "description")
        description.text = etree.CDATA(self.prefix + ad.description)

        # Добавляем изображения объявления
        images = etree.SubElement(car, "images")
        for photo_url in ad.get_photos():
            etree.SubElement(images, "image").text = photo_url

        # Добавляем видео, если оно есть
        if ad.video:
            video = etree.SubElement(car, "video")
            video.text = ad.video

        # Добавляем бейджи и контактную информацию салона
        badges = etree.SubElement(car, "badges")
        badge = etree.SubElement(badges, "badge")
        etree.SubElement(badge, "name").text = 'лучшее предложение месяца'

        contact_info = etree.SubElement(car, "contact_info")
        contact = etree.SubElement(contact_info, "contact")
        etree.SubElement(contact, "name").text = str(ad.salon.name)
        etree.SubElement(contact, "phone").text = str(ad.salon.telephone)
        etree.SubElement(contact, "time").text = str(ad.salon.working_hours)
        etree.SubElement(car, 'poi_id').text = str(ad.salon.address)

    def generate_xml(self, root: etree.Element) -> bytes:
        """
        Генерирует XML документ из корневого элемента и возвращает его в виде байтов.

        :param root: корневой элемент XML документа
        :return: XML документ в байтовом формате
        """
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8', method="xml")
