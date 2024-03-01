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
        # Получение параметров фильтрации из запроса
        print(request.query_params)
        selected_marks = request.query_params.getlist('marks')
        selected_models = request.query_params.getlist('models')
        # selected_modifications = request.query_params.getlist('modifications')
        # selected_bodies = request.query_params.getlist('bodies')
        # selected_configurations = request.query_params.getlist('configurations')
        # selected_colors = request.query_params.getlist('colors')
        # Фильтруем по выбранным маркам
        filtered_ads = Ad.objects.filter(mark__id__in=selected_marks)
        # Если выбраны модели, исключаем из марок те, по которым уже выбраны модели
        if selected_models:
            filtered_ads = Ad.objects.filter(model__id__in=selected_models)

        if not selected_marks:
            filtered_ads = Ad.objects.all()
        serializer = serializers.AdSerializer(filtered_ads, many=True)
        return Response(serializer.data)


class MarkListView(ListAPIView):
    queryset = Mark.objects.filter(ads__isnull=False).distinct()
    serializer_class = serializers.MarkSerializer


class ModelsByMarkView(ListAPIView):
    serializer_class = serializers.ModelSerializer  # Исправлено

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

        configurations = Ad.objects.filter(model_id__in=model_ids).values('configuration').distinct()
        return Response(configurations)


class ColorsByModelView(ListAPIView):
    def list(self, request, *args, **kwargs):
        model_ids = self.request.query_params.getlist('models')
        if not model_ids:
            return Response({'error': 'No models provided'}, status=status.HTTP_400_BAD_REQUEST)

        colors = Ad.objects.filter(model_id__in=model_ids).values('color').distinct()
        return Response(colors)

    # def get(self, request, *args, **kwargs):
    #     model_ids = self.request.query_params.getlist('models')
    #
    #     model_ids = [int(model_id) if model_id else '0' for model_id in model_ids[0].strip().split(',')]
    #
    #     query_condition = Q()
    #     for model_id in model_ids:
    #         query_condition |= Q(model_id=model_id)
    #     # Добавляются "серый" и "Серый"
    #     colors = Ad.objects.filter(query_condition).values_list('color', flat=True).distinct()
    #     return Response({'color': list(colors)}, status=status.HTTP_200_OK)
