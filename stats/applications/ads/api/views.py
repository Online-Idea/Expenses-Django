from functools import reduce

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from applications.ads.models import Ad
from libs.services.models import Model, Mark
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

        print(filters)
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
