import datetime
import pickle
import urllib.parse

import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.srav.filters import AutoruParsedAdFilter
from applications.srav.forms import AutoruParsedAdChooseForm, ComparisonChooseForm
from applications.srav.models import AutoruParsedAd, SravPivot
from applications.srav.serializers import AutoruParsedAdSerializer
from applications.srav.srav import get_srav_data, format_comparison
from libs.autoru.autoru import process_parsed_ads, fill_in_auction_with_parsed_ads, \
    fill_in_unique_cheapest_for_srav_pivot
from libs.services.decorators import allowed_users
from libs.services.utils import make_xlsx_for_download, get_all_fields_verbose_names


class AutoruParsedAdViewSet(viewsets.ModelViewSet):
    queryset = AutoruParsedAd.objects.all()
    serializer_class = AutoruParsedAdSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AutoruParsedAdFilter

    def create(self, request, *args, **kwargs):
        df_received, parser_datetime, region = pickle.loads(request.body)
        df_processed = process_parsed_ads(df_received, parser_datetime, region)

        serializer = self.get_serializer(data=df_processed, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Заполняю дилеров в аукционе по данным сравнительной
        fill_in_auction_with_parsed_ads(serializer.instance)

        # Заполняю сравнительную в этой базе
        fill_in_unique_cheapest_for_srav_pivot(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@allowed_users(allowed_groups=['admin'])
def parsed_ads(request):
    if request.method == 'POST':
        form = AutoruParsedAdChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(form.errors)

        context = get_srav_data(request, form, 'parsed_ads')

        return render(request, 'srav/parsed_ads.html', context)

    else:
        form = AutoruParsedAdChooseForm()

    today = datetime.date.today()
    context = {
        'form': form,
        'datefrom': today,
        'dateto': today,
    }

    return render(request, 'srav/parsed_ads.html', context)


@allowed_users(allowed_groups=['admin'])
def download_parsed_ads(request):
    if request.method == 'POST':
        form = AutoruParsedAdChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(form.errors)

        context = get_srav_data(request, form, 'parsed_ads')

        filter_params = context['filter_params']
        filter_params['datetime__gte'] = context['datefrom_dt']
        filter_params['datetime__lte'] = context['dateto_dt']
        filter_params.pop('daterange', None)

        columns = ['datetime', 'region', 'mark__mark', 'model__model', 'complectation', 'modification', 'year',
                   'dealer', 'price_with_discount', 'price_no_discount', 'with_nds', 'position_actual',
                   'position_total', 'link', 'condition', 'in_stock', 'services', 'tags', 'photos']

        queryset = (
            AutoruParsedAd.objects.prefetch_related(
                'mark', 'model'
            )
            .filter(**filter_params)
            .order_by('-datetime', 'region', 'mark', 'model', 'complectation', 'modification', 'year',
                      'position_actual')
            .values_list(*columns)
        )

        # Заголовки
        verbose_names = get_all_fields_verbose_names(AutoruParsedAd)
        headers = ['datetime', 'region', 'mark__mark', 'model__model', 'complectation', 'modification', 'year', 'dealer',
                   'price_with_discount', 'price_no_discount', 'with_nds', 'position_actual',
                   'position_total', 'link', 'condition', 'in_stock', 'services', 'tags', 'photos']
        headers = [verbose_names[header] for header in headers]

        # Файл
        wb = make_xlsx_for_download(queryset, headers)
        ws = wb['Sheet']
        ws.title = 'Выдача'

        wb = format_comparison(wb, ws.title)

        datefrom = datetime.date(*context['datefrom'][::-1]).strftime("%d.%m.%Y")
        dateto = datetime.date(*context['dateto'][::-1]).strftime("%d.%m.%Y")
        filename = f'Выдача {datefrom}-{dateto}.xlsx'
        filename = urllib.parse.quote(filename)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'

        wb.save(response)

        return response


@allowed_users(allowed_groups=['admin'])
def comparison(request):
    if request.method == 'POST':
        form = ComparisonChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(form.errors)

        context = get_srav_data(request, form, 'comparison')

        return render(request, 'srav/comparison.html', context)

    else:
        form = ComparisonChooseForm()

    today = datetime.date.today()
    context = {
        'form': form,
        'datefrom': today,
        'dateto': today,
    }
    return render(request, 'srav/comparison.html', context)


@allowed_users(allowed_groups=['admin'])
def download_comparison(request):
    if request.method == 'POST':
        form = ComparisonChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(form.errors)

        context = get_srav_data(request, form, 'comparison')

        filter_params = context['filter_params']
        filter_params['autoru_parsed_ad__datetime__gte'] = context['datefrom_dt']
        filter_params['autoru_parsed_ad__datetime__lte'] = context['dateto_dt']
        filter_params.pop('daterange', None)

        columns = ['autoru_parsed_ad__datetime', 'autoru_parsed_ad__region', 'autoru_parsed_ad__mark__mark',
                   'autoru_parsed_ad__model__model', 'autoru_parsed_ad__complectation',
                   'autoru_parsed_ad__modification', 'autoru_parsed_ad__year', 'autoru_parsed_ad__dealer',
                   'autoru_parsed_ad__price_with_discount', 'autoru_parsed_ad__price_no_discount',
                   'price_with_discount_diff', 'price_no_discount_diff',
                   'autoru_parsed_ad__with_nds', 'position_price',
                   'autoru_parsed_ad__position_actual', 'autoru_parsed_ad__link',
                   'in_stock_count', 'for_order_count']

        queryset = (
            SravPivot.objects.prefetch_related('autoru_parsed_ad')
            .filter(**filter_params)
            .order_by('-autoru_parsed_ad__datetime', 'autoru_parsed_ad__region', 'autoru_parsed_ad__mark',
                      'autoru_parsed_ad__model', 'autoru_parsed_ad__complectation', 'autoru_parsed_ad__modification',
                      'autoru_parsed_ad__year', 'position_price')
            .values(*list(filter(lambda x: x not in ['price_with_discount_diff', 'price_no_discount_diff'], columns)))
        )

        # Считаю разницу
        df = pd.DataFrame.from_records(queryset)
        lookup_df = df[df['autoru_parsed_ad__dealer'] == context['dealer_for_comparison']]
        merged_df = pd.merge(df, lookup_df, on=[
            'autoru_parsed_ad__mark__mark', 'autoru_parsed_ad__model__model', 'autoru_parsed_ad__complectation',
            'autoru_parsed_ad__modification', 'autoru_parsed_ad__year'
        ], suffixes=('_data', '_lookup'), how='left')

        merged_df['price_with_discount_diff'] = merged_df['autoru_parsed_ad__price_with_discount_data'] - merged_df[
            'autoru_parsed_ad__price_with_discount_lookup']
        merged_df['price_no_discount_diff'] = merged_df['autoru_parsed_ad__price_no_discount_data'] - merged_df[
            'autoru_parsed_ad__price_no_discount_lookup']

        # Удаляю столбцы по которым считал разницы
        merged_df = merged_df.filter(regex='^(?!.*_lookup)')

        # Убираю более ненужные суффиксы
        merged_df.columns = merged_df.columns.str.replace('_data', '')

        # Меняю столбцы местами
        merged_df = merged_df[['autoru_parsed_ad__datetime', 'autoru_parsed_ad__region', 'autoru_parsed_ad__mark__mark',
                               'autoru_parsed_ad__model__model', 'autoru_parsed_ad__complectation',
                               'autoru_parsed_ad__modification', 'autoru_parsed_ad__year', 'autoru_parsed_ad__dealer',
                               'autoru_parsed_ad__price_with_discount', 'autoru_parsed_ad__price_no_discount',
                               'price_with_discount_diff', 'price_no_discount_diff',
                               'autoru_parsed_ad__with_nds', 'position_price',
                               'autoru_parsed_ad__position_actual', 'autoru_parsed_ad__link',
                               'in_stock_count', 'for_order_count']]

        data_as_tuples = merged_df.to_records(index=False).tolist()

        # Заголовки
        verbose_names = get_all_fields_verbose_names(SravPivot)
        verbose_names['price_with_discount_diff'] = 'Разница цены со скидками'
        verbose_names['price_no_discount_diff'] = 'Разница цены без скидок'
        headers = [verbose_names[column] for column in columns]

        # Файл
        wb = make_xlsx_for_download(data_as_tuples, headers)
        ws = wb['Sheet']
        ws.title = 'Сравнительная'

        wb = format_comparison(wb, ws.title, context['dealer_for_comparison'])

        datefrom = datetime.date(*context['datefrom'][::-1]).strftime("%d.%m.%Y")
        dateto = datetime.date(*context['dateto'][::-1]).strftime("%d.%m.%Y")
        filename = f'Сравнительная {datefrom}-{dateto}.xlsx'
        filename = urllib.parse.quote(filename)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
        wb.save(response)

        return response


@allowed_users(allowed_groups=['admin'])
def get_dealers_for_comparison(request):
    date = request.query_params.get('date')
    marks = request.query_params.getlist('marks')
    regions = request.query_params.getlist('regions')

    salons = AutoruParsedAd.objects.filter(mark__in=marks, regions__in=regions)
    salons_dict = dict(salons)

    return JsonResponse(salons_dict)


class DealersForSravView(APIView):
    def get(self, request, format=None):
        datefrom = request.query_params.get('datefrom')
        datefrom = datetime.datetime.strptime(datefrom, '%Y-%m-%d')
        datefrom = datefrom.replace(hour=0, minute=0)
        dateto = request.query_params.get('dateto')
        dateto = datetime.datetime.strptime(dateto, '%Y-%m-%d')
        dateto = dateto.replace(hour=23, minute=59)

        marks = request.query_params.getlist('marks[]')
        regions = request.query_params.getlist('regions[]')

        dealers = AutoruParsedAd.objects.filter(
                datetime__gte=datefrom, datetime__lte=dateto,
                mark__in=marks, region__in=regions
            ) \
            .order_by('dealer') \
            .values_list('dealer', flat=True).distinct()

        return Response(dealers)
